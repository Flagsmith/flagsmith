import json
import re
from datetime import UTC, datetime, timedelta
from typing import Callable, Protocol
from unittest.mock import Mock

import freezegun
import pytest
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from requests.exceptions import RequestException
from rest_framework.test import APIClient

from core.signals import create_audit_log_from_historical_record
from features.models import FeatureState
from integrations.sentry.change_tracking import requests  # type: ignore[attr-defined]
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


@pytest.fixture(autouse=True)
def requests_post(mocker: MockerFixture) -> Mock:
    return mocker.patch.object(requests, "post")


class AssertLogsCallable(Protocol):
    def __call__(self, *expected_logs: tuple[str, str, str, str]) -> None: ...


@pytest.fixture
def assert_logs(log: StructuredLogCapture) -> AssertLogsCallable:
    def _assert_logs(*expected_logs: tuple[str, str, str, str]) -> None:
        logs = (
            (e["level"], e["event"], e["sentry_action"], e["feature_name"])
            for e in log.events
        )
        for event in expected_logs:
            assert event in logs

    return _assert_logs


def test_sentry_change_tracking__flag_created__sends_update_to_sentry(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    assert_logs: AssertLogsCallable,
    feature_name: str,
    mocker: MockerFixture,
    project: int,
    requests_post: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    requests_post.return_value.status_code = 200
    requests_post.return_value.text = ""

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
    feature_state = FeatureState.objects.get(feature_id=response.json()["id"])
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
                        "change_id": str(feature_state.pk),
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
    assert_logs(
        ("debug", "sending", "created", feature_name),
        ("info", "success", "created", feature_name),
    )


def test_sentry_change_tracking__flag_state_change__sends_update_to_sentry(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    assert_logs: AssertLogsCallable,
    environment_api_key: str,
    feature_name: str,
    feature_state: int,
    mocker: MockerFixture,
    requests_post: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    requests_post.return_value.status_code = 200
    requests_post.return_value.text = ""

    # When
    with freezegun.freeze_time("2199-01-01T00:00:00.500000+00:00"):
        response = admin_client.patch(
            path=f"/api/v1/environments/{environment_api_key}/featurestates/{feature_state}/",
            format="json",
            data={"enabled": True},
        )

    # Then
    assert response.status_code == 200, response.content
    requests_post.assert_called_with(
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
    assert_logs(
        ("debug", "sending", "updated", feature_name),
        ("info", "success", "updated", feature_name),
    )


def test_sentry_change_tracking__flag_state_schedule__sends_update_to_sentry(
    admin_user: FFAdminUser,
    assert_logs: AssertLogsCallable,
    feature_name: str,
    feature_state: int,
    mocker: MockerFixture,
    requests_post: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    feature_state_obj = FeatureState.objects.get(pk=feature_state)
    requests_post.return_value.status_code = 200
    requests_post.return_value.text = ""

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
    assert [
        json.loads(kwargs["data"])["data"][0]["action"]
        for args, kwargs in requests_post.call_args_list
    ] == ["created"]  # No "updated" yet

    # When
    with freezegun.freeze_time("2199-01-01T01:00:01.500000+00:00"):
        create_audit_log_from_historical_record(
            instance=feature_state_obj,
            history_user=admin_user,
            history_instance=feature_state_obj.history.first(),
        )

    # Then
    requests_post.assert_called_with(
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
    assert_logs(
        ("debug", "sending", "updated", feature_name),
        ("info", "success", "updated", feature_name),
    )


def test_sentry_change_tracking__flag_deleted__sends_update_to_sentry(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    assert_logs: AssertLogsCallable,
    environment_api_key: str,
    feature_name: str,
    feature_state: int,
    mocker: MockerFixture,
    requests_post: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    requests_post.return_value.status_code = 200
    requests_post.return_value.text = ""

    # When
    with freezegun.freeze_time("2199-01-01T01:00:00+00:00"):
        response = admin_client.delete(
            path=f"/api/v1/environments/{environment_api_key}/featurestates/{feature_state}/",
        )

    # Then
    assert response.status_code == 204, response.content
    requests_post.assert_called_with(
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
    assert_logs(
        ("debug", "sending", "deleted", feature_name),
        ("info", "success", "deleted", feature_name),
    )


@pytest.mark.parametrize(
    "error_log_event, sentry_fail",
    [
        (
            "request-failure",
            lambda post: setattr(
                post,
                "side_effect",
                RequestException("Bad Sentry! Or is my Internet? :("),
            ),
        ),
        (
            "request-failure",
            lambda post: setattr(
                post.return_value.raise_for_status,
                "side_effect",
                RequestException("Oof"),
            ),
        ),
        (
            "integration-error",
            lambda post: setattr(
                post.return_value,
                "text",
                '{"data":[{"change_id":["Field is required."]}]}',
            ),
        ),
    ],
)
def test_sentry_change_tracking__failing_integration__fails_gracefully(
    admin_client: APIClient,
    assert_logs: AssertLogsCallable,
    environment_api_key: str,
    error_log_event: str,
    feature_name: str,
    feature_state: int,
    requests_post: Mock,
    sentry_fail: Callable[[Mock], None],
) -> None:
    # Given
    requests_post.return_value.status_code = 200  # Sentry always responds 200 OK :(
    sentry_fail(requests_post)

    # When
    response = admin_client.patch(
        path=f"/api/v1/environments/{environment_api_key}/featurestates/{feature_state}/",
        format="json",
        data={"enabled": True},
    )

    # Then
    assert response.status_code == 200, response.content
    assert requests_post.called
    assert_logs(
        ("debug", "sending", "updated", feature_name),
        ("warning", error_log_event, "updated", feature_name),
    )
