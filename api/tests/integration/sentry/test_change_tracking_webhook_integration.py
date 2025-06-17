import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import ANY

import freezegun
import pytest
from pytest_structlog import StructuredLogCapture
from responses import RequestsMock
from rest_framework.test import APIClient

from core.signals import create_audit_log_from_historical_record
from features.models import FeatureState
from integrations.sentry.models import SentryChangeTrackingConfiguration
from users.models import FFAdminUser


@pytest.fixture(autouse=True)
def sentry_configuration(environment: int) -> SentryChangeTrackingConfiguration:
    configuration = SentryChangeTrackingConfiguration(
        environment_id=environment,
        webhook_url="https://sentry.example.com/webhook",
        secret="hush hush!",
    )
    configuration.save()
    return configuration


def test_sentry_change_tracking__flag_created__sends_update_to_sentry(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    feature_name: str,
    log: StructuredLogCapture,
    project: int,
    responses: RequestsMock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    responses.post(sentry_configuration.webhook_url, status=200, body="")

    # When
    with freezegun.freeze_time("2199-01-01T00:00:00.500000+00:00"):
        response = admin_client.post(
            path=f"/api/v1/projects/{project}/features/",
            format="json",
            data={
                "name": feature_name,
            },
        )

    # Then
    assert response.status_code == 201, response.content
    assert len(responses.calls) == 1
    create_request = responses.calls[0].request  # type: ignore[union-attr]
    assert create_request.url == sentry_configuration.webhook_url
    assert create_request.headers["Content-Type"] == "application/json"
    assert re.match(r"^[0-9a-f]{64}$", create_request.headers["X-Sentry-Signature"])
    feature_state_obj = FeatureState.objects.get(feature_id=response.json()["id"])
    assert json.loads(create_request.body) == {
        "data": [
            {
                "action": "created",
                "created_at": "2199-01-01T00:00:00+00:00",
                "created_by": {"id": admin_user.email, "type": "email"},
                "change_id": str(feature_state_obj.pk),
                "flag": feature_name,
            },
        ],
        "meta": {"version": 1},
    }
    assert log.events == [
        {
            "event": "sending",
            "feature_name": feature_name,
            "headers": ANY,
            "level": "debug",
            "payload": ANY,
            "sentry_action": "created",
            "url": sentry_configuration.webhook_url,
        },
        {
            "event": "success",
            "feature_name": feature_name,
            "level": "info",
            "sentry_action": "created",
        },
    ]


def test_sentry_change_tracking__flag_state_change__sends_update_to_sentry(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    environment_api_key: str,
    feature_name: str,
    feature_state: int,
    log: StructuredLogCapture,
    responses: RequestsMock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    responses.post(sentry_configuration.webhook_url, status=200, body="")

    # When
    with freezegun.freeze_time("2199-01-01T00:00:00.500000+00:00"):
        response = admin_client.patch(
            path=f"/api/v1/environments/{environment_api_key}/featurestates/{feature_state}/",
            format="json",
            data={"enabled": True},
        )

    # Then
    assert response.status_code == 200, response.content
    assert len(responses.calls) == 1
    update_request = responses.calls[0].request  # type: ignore[union-attr]
    assert update_request.url == sentry_configuration.webhook_url
    assert update_request.headers["Content-Type"] == "application/json"
    assert re.match(r"^[0-9a-f]{64}$", update_request.headers["X-Sentry-Signature"])
    assert json.loads(update_request.body) == {
        "data": [
            {
                "action": "updated",
                "created_at": "2199-01-01T00:00:00+00:00",
                "created_by": {"id": admin_user.email, "type": "email"},
                "change_id": str(feature_state),
                "flag": feature_name,
            },
        ],
        "meta": {"version": 1},
    }
    assert log.events == [
        {
            "event": "sending",
            "feature_name": feature_name,
            "headers": ANY,
            "level": "debug",
            "payload": ANY,
            "sentry_action": "updated",
            "url": sentry_configuration.webhook_url,
        },
        {
            "event": "success",
            "feature_name": feature_name,
            "level": "info",
            "sentry_action": "updated",
        },
    ]


def test_sentry_change_tracking__flag_state_schedule__sends_update_to_sentry(
    admin_user: FFAdminUser,
    feature_name: str,
    feature_state: int,
    log: StructuredLogCapture,
    responses: RequestsMock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    feature_state_obj = FeatureState.objects.get(pk=feature_state)
    responses.post(sentry_configuration.webhook_url, status=200, body="")

    # When
    with freezegun.freeze_time("2199-01-01T00:00:00.500000+00:00"):
        now = datetime.now(UTC)
        feature_state_obj.enabled = False
        feature_state_obj.live_from = now + timedelta(hours=1)
        feature_state_obj.save()
        create_audit_log_from_historical_record(
            instance=feature_state_obj,
            history_user=admin_user,
            history_instance=feature_state_obj.history.first(),
        )

    # Then
    assert len(responses.calls) == 0  # Not yet

    # When
    with freezegun.freeze_time("2199-01-01T01:00:01.500000+00:00"):
        create_audit_log_from_historical_record(
            instance=feature_state_obj,
            history_user=admin_user,
            history_instance=feature_state_obj.history.first(),
        )

    # Then
    assert len(responses.calls) == 1
    update_request = responses.calls[0].request  # type: ignore[union-attr]
    assert update_request.url == sentry_configuration.webhook_url
    assert update_request.headers["Content-Type"] == "application/json"
    assert re.match(r"^[0-9a-f]{64}$", update_request.headers["X-Sentry-Signature"])
    assert json.loads(update_request.body) == {
        "data": [
            {
                "action": "updated",
                "created_at": "2199-01-01T01:00:00+00:00",
                "created_by": {"id": admin_user.email, "type": "email"},
                "change_id": str(feature_state),
                "flag": feature_name,
            },
        ],
        "meta": {"version": 1},
    }
    assert log.events == [
        {
            "event": "sending",
            "feature_name": feature_name,
            "headers": ANY,
            "level": "debug",
            "payload": ANY,
            "sentry_action": "updated",
            "url": sentry_configuration.webhook_url,
        },
        {
            "event": "success",
            "feature_name": feature_name,
            "level": "info",
            "sentry_action": "updated",
        },
    ]


def test_sentry_change_tracking__flag_deleted__sends_update_to_sentry(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    environment_api_key: str,
    feature_name: str,
    feature_state: int,
    log: StructuredLogCapture,
    responses: RequestsMock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    responses.post(sentry_configuration.webhook_url, status=200, body="")

    # When
    with freezegun.freeze_time("2199-01-01T00:00:00+00:00"):
        response = admin_client.delete(
            path=f"/api/v1/environments/{environment_api_key}/featurestates/{feature_state}/",
        )

    # Then
    assert response.status_code == 204, response.content
    assert len(responses.calls) == 1
    delete_request = responses.calls[0].request  # type: ignore[union-attr]
    assert delete_request.url == sentry_configuration.webhook_url
    assert delete_request.headers["Content-Type"] == "application/json"
    assert re.match(r"^[0-9a-f]{64}$", delete_request.headers["X-Sentry-Signature"])
    assert json.loads(delete_request.body) == {
        "data": [
            {
                "action": "deleted",
                "created_at": "2199-01-01T00:00:00+00:00",
                "created_by": {"id": admin_user.email, "type": "email"},
                "change_id": str(feature_state),
                "flag": feature_name,
            },
        ],
        "meta": {"version": 1},
    }
    assert log.events == [
        {
            "event": "sending",
            "feature_name": feature_name,
            "headers": ANY,
            "level": "debug",
            "payload": ANY,
            "sentry_action": "deleted",
            "url": sentry_configuration.webhook_url,
        },
        {
            "event": "success",
            "feature_name": feature_name,
            "level": "info",
            "sentry_action": "deleted",
        },
    ]


@pytest.mark.parametrize(
    "error_log, sentry_response",
    [
        (
            {"event": "request-failure", "error": ANY},
            {"status": 502},
        ),
        (
            {
                "event": "integration-error",
                "sentry_response_body": '{"data":[{"change_id":["Field is required."]}]}',
                "sentry_response_status": 200,
            },
            {
                "status": 200,
                "body": '{"data":[{"change_id":["Field is required."]}]}',
            },
        ),
    ],
)
def test_sentry_change_tracking__failing_integration__fails_gracefully(
    admin_client: APIClient,
    environment_api_key: str,
    error_log: dict[str, Any],
    feature_name: str,
    feature_state: int,
    log: StructuredLogCapture,
    responses: RequestsMock,
    sentry_response: dict[str, Any],
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    responses.post(sentry_configuration.webhook_url, **sentry_response)

    # When
    response = admin_client.patch(
        path=f"/api/v1/environments/{environment_api_key}/featurestates/{feature_state}/",
        format="json",
        data={"enabled": True},
    )

    # Then
    assert response.status_code == 200, response.content
    assert len(responses.calls) == 1
    assert log.events == [
        {
            "event": "sending",
            "feature_name": feature_name,
            "headers": ANY,
            "level": "debug",
            "payload": ANY,
            "sentry_action": "updated",
            "url": sentry_configuration.webhook_url,
        },
        {
            "feature_name": feature_name,
            "level": "warning",
            "sentry_action": "updated",
            **error_log,
        },
    ]
