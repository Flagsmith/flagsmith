import json
import logging
import re
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import freezegun
import pytest
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture
from requests.exceptions import RequestException
from rest_framework.test import APIClient

from core.signals import create_audit_log_from_historical_record
from features.models import FeatureState
from integrations.sentry.change_tracking import requests  # type: ignore[attr-defined]
from integrations.sentry.models import SentryChangeTrackingConfiguration
from users.models import FFAdminUser


@pytest.fixture
def sentry_configuration(environment: int) -> SentryChangeTrackingConfiguration:
    configuration = SentryChangeTrackingConfiguration(
        environment_id=environment,
        webhook_url="https://sentry.example.com/webhook",
        secret="hush hush!",
    )
    configuration.save()
    return configuration


@pytest.fixture
def requests_post(mocker: MockerFixture) -> Mock:
    return mocker.patch.object(requests, "post")


def test_sentry_change_tracking__flag_created__sends_update_to_sentry(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    caplog: LogCaptureFixture,
    feature_name: str,
    mocker: MockerFixture,
    project: int,
    requests_post: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    caplog.set_level(logging.DEBUG)

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
    assert response.status_code == 201
    requests_post.assert_called_once_with(
        url=sentry_configuration.webhook_url,
        headers={
            "Content-Type": "application/json",
            "X-Sentry-Signature": mocker.ANY,
        },
        data=json.dumps(
            {
                "data": [
                    {
                        "action": "created",
                        "created_at": "2199-01-01T00:00:00+00:00",
                        "created_by": {"id": admin_user.email, "type": "email"},
                        "flag": feature_name,
                    },
                ],
                "meta": {"version": 1},
            },
            sort_keys=True,
        ),
    )
    signature = requests_post.call_args[1]["headers"]["X-Sentry-Signature"]
    assert re.match(r"^[0-9a-f]{64}$", signature)
    logs = ((record.levelname, record.message) for record in caplog.records)
    assert ("DEBUG", f"Sending '{feature_name}' (created) to Sentry...") in logs
    assert ("DEBUG", f"Sent '{feature_name}' (created) to Sentry") in logs


def test_sentry_change_tracking__flag_state_change__sends_update_to_sentry(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    caplog: LogCaptureFixture,
    environment_api_key: str,
    feature_name: str,
    feature_state: int,
    mocker: MockerFixture,
    requests_post: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    caplog.set_level(logging.DEBUG)

    # When
    with freezegun.freeze_time("2199-01-01T00:00:00.500000+00:00"):
        response = admin_client.patch(
            path=f"/api/v1/environments/{environment_api_key}/featurestates/{feature_state}/",
            format="json",
            data={"enabled": True},
        )

    # Then
    assert response.status_code == 200
    requests_post.assert_called_once_with(
        url=sentry_configuration.webhook_url,
        headers={
            "Content-Type": "application/json",
            "X-Sentry-Signature": mocker.ANY,
        },
        data=json.dumps(
            {
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
            },
            sort_keys=True,
        ),
    )
    signature = requests_post.call_args[1]["headers"]["X-Sentry-Signature"]
    assert re.match(r"^[0-9a-f]{64}$", signature)
    logs = ((record.levelname, record.message) for record in caplog.records)
    assert ("DEBUG", f"Sending '{feature_name}' (updated) to Sentry...") in logs
    assert ("DEBUG", f"Sent '{feature_name}' (updated) to Sentry") in logs


def test_sentry_change_tracking__flag_state_schedule__sends_update_to_sentry(
    admin_user: FFAdminUser,
    caplog: LogCaptureFixture,
    feature_name: str,
    feature_state: int,
    mocker: MockerFixture,
    requests_post: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    caplog.set_level(logging.DEBUG)
    feature_state_obj = FeatureState.objects.get(pk=feature_state)

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
    assert not requests_post.called  # Yet

    # When
    with freezegun.freeze_time("2199-01-01T01:00:01.500000+00:00"):
        create_audit_log_from_historical_record(
            instance=feature_state_obj,
            history_user=admin_user,
            history_instance=feature_state_obj.history.first(),
        )

    # Then
    requests_post.assert_called_once_with(
        url=sentry_configuration.webhook_url,
        headers={
            "Content-Type": "application/json",
            "X-Sentry-Signature": mocker.ANY,
        },
        data=json.dumps(
            {
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
            },
            sort_keys=True,
        ),
    )
    signature = requests_post.call_args[1]["headers"]["X-Sentry-Signature"]
    assert re.match(r"^[0-9a-f]{64}$", signature)
    logs = ((record.levelname, record.message) for record in caplog.records)
    assert ("DEBUG", f"Sending '{feature_name}' (updated) to Sentry...") in logs
    assert ("DEBUG", f"Sent '{feature_name}' (updated) to Sentry") in logs


def test_sentry_change_tracking__flag_deleted__sends_update_to_sentry(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    caplog: LogCaptureFixture,
    environment_api_key: str,
    feature_name: str,
    feature_state: int,
    mocker: MockerFixture,
    requests_post: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    caplog.set_level(logging.DEBUG)

    # When
    with freezegun.freeze_time("2199-01-01T01:00:00+00:00"):
        response = admin_client.delete(
            path=f"/api/v1/environments/{environment_api_key}/featurestates/{feature_state}/",
        )

    # Then
    assert response.status_code == 204
    requests_post.assert_called_once_with(
        url=sentry_configuration.webhook_url,
        headers={
            "Content-Type": "application/json",
            "X-Sentry-Signature": mocker.ANY,
        },
        data=json.dumps(
            {
                "data": [
                    {
                        "action": "deleted",
                        "created_at": "2199-01-01T01:00:00+00:00",
                        "created_by": {"id": admin_user.email, "type": "email"},
                        "flag": feature_name,
                    },
                ],
                "meta": {"version": 1},
            },
            sort_keys=True,
        ),
    )
    signature = requests_post.call_args[1]["headers"]["X-Sentry-Signature"]
    assert re.match(r"^[0-9a-f]{64}$", signature)
    logs = ((record.levelname, record.message) for record in caplog.records)
    assert ("DEBUG", f"Sending '{feature_name}' (deleted) to Sentry...") in logs
    assert ("DEBUG", f"Sent '{feature_name}' (deleted) to Sentry") in logs


def test_sentry_change_tracking__failing_integration__fails_gracefully(
    admin_client: APIClient,
    caplog: LogCaptureFixture,
    environment_api_key: str,
    feature_name: str,
    feature_state: int,
    mocker: MockerFixture,
    requests_post: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    caplog.set_level(logging.DEBUG)
    sentry_error = RequestException("Bad Sentry")
    requests_post.return_value.raise_for_status.side_effect = sentry_error

    # When
    response = admin_client.patch(
        path=f"/api/v1/environments/{environment_api_key}/featurestates/{feature_state}/",
        format="json",
        data={"enabled": True},
    )

    # Then
    assert response.status_code == 200
    assert requests_post.called
    logs = ((record.levelname, record.message) for record in caplog.records)
    assert ("DEBUG", f"Sending '{feature_name}' (updated) to Sentry...") in logs
    assert (
        "ERROR",
        f"Error sending '{feature_name}' (updated) to Sentry: RequestException('Bad Sentry')",
    ) in logs
