import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import ANY

import freezegun
import pytest
from django.urls import reverse
from pytest_structlog import StructuredLogCapture
from responses import RequestsMock
from rest_framework.test import APIClient

from audit.tasks import create_feature_state_updated_by_change_request_audit_log
from features.models import FeatureState
from features.versioning.tasks import enable_v2_versioning
from features.workflows.core.models import ChangeRequest
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


@pytest.fixture()
def v2_versioned_environment(environment: int) -> int:
    enable_v2_versioning(environment_id=environment)
    return environment


@pytest.mark.parametrize(
    "use_v2_versioning",
    [pytest.param(False, id="v1"), pytest.param(True, id="v2")],
)
def test_sentry_change_tracking__flag_created__sends_update_to_sentry(
    use_v2_versioning: bool,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    environment: int,
    feature_name: str,
    log: StructuredLogCapture,
    project: int,
    responses: RequestsMock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    if use_v2_versioning:
        enable_v2_versioning(environment_id=environment)
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


def test_sentry_change_tracking__flag_state_change__v2_versioning__sends_update_to_sentry(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    environment: int,
    feature: int,
    feature_name: str,
    log: StructuredLogCapture,
    responses: RequestsMock,
    sentry_configuration: SentryChangeTrackingConfiguration,
    v2_versioned_environment: int,
) -> None:
    # Given
    responses.post(sentry_configuration.webhook_url, status=200, body="")

    create_ef_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment, feature],
    )
    list_ef_version_fs_url_template = (
        "api-v1:versioning:environment-feature-version-featurestates-list"
    )
    detail_ef_version_fs_url_template = (
        "api-v1:versioning:environment-feature-version-featurestates-detail"
    )

    # When
    with freezegun.freeze_time("2199-01-01T00:00:00.500000+00:00"):
        # Create a new EFV draft
        create_response = admin_client.post(create_ef_version_url)
        assert create_response.status_code == 201, create_response.content
        ef_version_uuid = create_response.json()["uuid"]

        # Look up the cloned feature state on the new EFV
        list_fs_response = admin_client.get(
            reverse(
                list_ef_version_fs_url_template,
                args=[environment, feature, ef_version_uuid],
            )
        )
        assert list_fs_response.status_code == 200, list_fs_response.content
        new_feature_state_id = list_fs_response.json()[0]["id"]

        # Toggle the flag enabled in the new version
        update_response = admin_client.patch(
            reverse(
                detail_ef_version_fs_url_template,
                args=[
                    environment,
                    feature,
                    ef_version_uuid,
                    new_feature_state_id,
                ],
            ),
            data=json.dumps({"enabled": True}),
            content_type="application/json",
        )
        assert update_response.status_code == 200, update_response.content

        # Publish the new version
        publish_response = admin_client.post(
            reverse(
                "api-v1:versioning:environment-feature-versions-publish",
                args=[environment, feature, ef_version_uuid],
            )
        )
        assert publish_response.status_code == 200, publish_response.content

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
                "created_at": "2199-01-01T00:00:00+00:00",
                "created_by": {"id": admin_user.email, "type": "email"},
                "change_id": str(new_feature_state_id),
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
    environment: int,
) -> None:
    # Given
    cr = ChangeRequest.objects.create(
        environment_id=environment, title="Test CR", user_id=admin_user.id
    )
    feature_state_obj = FeatureState.objects.get(pk=feature_state)
    feature_state_obj.change_request = cr
    feature_state_obj.save()
    responses.post(sentry_configuration.webhook_url, status=200, body="")

    # When
    with freezegun.freeze_time("2199-01-01T00:00:00.500000+00:00"):
        now = datetime.now(UTC)
        feature_state_obj.enabled = False
        feature_state_obj.live_from = now + timedelta(hours=1)
        feature_state_obj.save()
        create_feature_state_updated_by_change_request_audit_log(feature_state_obj.id)

    # Then
    assert len(responses.calls) == 0  # Not yet

    # When
    with freezegun.freeze_time("2199-01-01T01:00:01.500000+00:00"):
        create_feature_state_updated_by_change_request_audit_log(feature_state_obj.id)

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
                "created_by": {"id": "app@flagsmith.com", "type": "email"},
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


def test_sentry_change_tracking__flag_state_schedule__v2_versioning__sends_update_to_sentry(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    environment: int,
    feature: int,
    feature_name: str,
    log: StructuredLogCapture,
    responses: RequestsMock,
    sentry_configuration: SentryChangeTrackingConfiguration,
    v2_versioned_environment: int,
) -> None:
    # Given
    responses.post(sentry_configuration.webhook_url, status=200, body="")

    create_ef_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment, feature],
    )

    # When — author + publish a scheduled v2 change with a future live_from
    with freezegun.freeze_time("2199-01-01T00:00:00.500000+00:00"):
        create_response = admin_client.post(create_ef_version_url)
        assert create_response.status_code == 201, create_response.content
        ef_version_uuid = create_response.json()["uuid"]

        list_fs_response = admin_client.get(
            reverse(
                "api-v1:versioning:environment-feature-version-featurestates-list",
                args=[environment, feature, ef_version_uuid],
            )
        )
        assert list_fs_response.status_code == 200, list_fs_response.content
        new_feature_state_id = list_fs_response.json()[0]["id"]

        update_response = admin_client.patch(
            reverse(
                "api-v1:versioning:environment-feature-version-featurestates-detail",
                args=[
                    environment,
                    feature,
                    ef_version_uuid,
                    new_feature_state_id,
                ],
            ),
            data=json.dumps({"enabled": True}),
            content_type="application/json",
        )
        assert update_response.status_code == 200, update_response.content

        # Publish the version with a future live_from (one hour ahead)
        publish_response = admin_client.post(
            reverse(
                "api-v1:versioning:environment-feature-versions-publish",
                args=[environment, feature, ef_version_uuid],
            ),
            data=json.dumps({"live_from": "2199-01-01T01:00:00+00:00"}),
            content_type="application/json",
        )
        assert publish_response.status_code == 200, publish_response.content

    # Then — Sentry should be notified about the scheduled v2 change
    # (timing relative to live_from is left to the implementation; this test
    # asserts that the notification happens at all)
    assert len(responses.calls) == 1
    update_request = responses.calls[0].request  # type: ignore[union-attr]
    assert update_request.url == sentry_configuration.webhook_url
    assert update_request.headers["Content-Type"] == "application/json"
    assert re.match(r"^[0-9a-f]{64}$", update_request.headers["X-Sentry-Signature"])
    payload = json.loads(update_request.body)
    assert payload["data"][0]["action"] == "updated"
    assert payload["data"][0]["change_id"] == str(new_feature_state_id)
    assert payload["data"][0]["flag"] == feature_name
    assert payload["data"][0]["created_by"] == {
        "id": admin_user.email,
        "type": "email",
    }


@pytest.mark.parametrize(
    "use_v2_versioning",
    [pytest.param(False, id="v1"), pytest.param(True, id="v2")],
)
def test_sentry_change_tracking__flag_deleted__sends_update_to_sentry(
    use_v2_versioning: bool,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    environment: int,
    environment_api_key: str,
    feature_name: str,
    feature_state: int,
    log: StructuredLogCapture,
    responses: RequestsMock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    if use_v2_versioning:
        enable_v2_versioning(environment_id=environment)
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
