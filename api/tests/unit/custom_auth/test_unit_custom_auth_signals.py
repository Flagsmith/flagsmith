import json
from unittest.mock import MagicMock

import openfeature.api as openfeature_api
import pytest
from djoser.signals import user_activated  # type: ignore[import-untyped]
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from users.models import FFAdminUser

SIGNUP_ANONYMOUS_ID = "6f1c5d2e-3b4a-4c8d-9e0f-1a2b3c4d5e6f"


@pytest.fixture()
def mock_openfeature_client(mocker: MockerFixture) -> MagicMock:
    mock_client: MagicMock = mocker.MagicMock()
    mocker.patch(
        "custom_auth.signals.get_openfeature_client",
        return_value=mock_client,
    )
    return mock_client


def test_user_activated__signup_anonymous_id_stored__tracks_conversion(
    admin_user: FFAdminUser,
    mock_openfeature_client: MagicMock,
) -> None:
    # Given
    admin_user.onboarding_data = json.dumps(
        {"signup_anonymous_id": SIGNUP_ANONYMOUS_ID}
    )

    # When
    user_activated.send(sender=FFAdminUser, user=admin_user, request=None)

    # Then
    mock_openfeature_client.track.assert_called_once()
    call_args = mock_openfeature_client.track.call_args
    assert call_args.args == ("signup_activated",)
    assert call_args.kwargs["evaluation_context"].targeting_key == SIGNUP_ANONYMOUS_ID


@pytest.mark.parametrize(
    "onboarding_data",
    [None, json.dumps({"tasks": [{"name": "task-1"}]})],
)
def test_user_activated__no_signup_anonymous_id__does_not_track(
    admin_user: FFAdminUser,
    mock_openfeature_client: MagicMock,
    onboarding_data: str | None,
) -> None:
    # Given
    admin_user.onboarding_data = onboarding_data

    # When
    user_activated.send(sender=FFAdminUser, user=admin_user, request=None)

    # Then
    mock_openfeature_client.track.assert_not_called()


@pytest.mark.parametrize(
    "onboarding_data",
    [json.dumps({"signup_anonymous_id": SIGNUP_ANONYMOUS_ID}), "not-json", "1"],
)
def test_user_activated__tracking_or_parsing_fails__logs_and_does_not_raise(
    admin_user: FFAdminUser,
    mock_openfeature_client: MagicMock,
    log: StructuredLogCapture,
    onboarding_data: str,
) -> None:
    # Given
    admin_user.onboarding_data = onboarding_data
    mock_openfeature_client.track.side_effect = RuntimeError("boom")

    # When
    user_activated.send(sender=FFAdminUser, user=admin_user, request=None)

    # Then
    assert log.events == [
        {
            "level": "error",
            "event": "conversion.tracking_failed",
            "user__id": admin_user.id,
            "exc_info": True,
        }
    ]


def test_user_activated__events_disabled__does_not_raise(
    admin_user: FFAdminUser,
    settings: SettingsWrapper,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_OFFLINE_MODE = True
    openfeature_api.clear_providers()
    admin_user.onboarding_data = json.dumps(
        {"signup_anonymous_id": SIGNUP_ANONYMOUS_ID}
    )

    # When
    user_activated.send(sender=FFAdminUser, user=admin_user, request=None)

    # Then
    assert log.events == []
