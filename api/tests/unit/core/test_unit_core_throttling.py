from unittest.mock import MagicMock

from pytest_mock import MockerFixture
from rest_framework.request import Request

from api_keys.models import MasterAPIKey
from api_keys.user import APIKeyUser
from core.throttling import MasterAPIKeyUserRateThrottle
from users.models import FFAdminUser


def test_master_api_key_user_rate_throttle__master_api_key_user__throttled(
    mocker: MockerFixture,
    admin_master_api_key_object: MasterAPIKey,
) -> None:
    # Given
    throttle = MasterAPIKeyUserRateThrottle()
    user = APIKeyUser(admin_master_api_key_object)

    mock_request = MagicMock(spec=Request)
    mock_request.user = user

    mock_view = MagicMock()

    mock_parent_allow_request = mocker.patch(
        "rest_framework.throttling.UserRateThrottle.allow_request",
        return_value=False,
    )

    # When
    result = throttle.allow_request(mock_request, mock_view)

    # Then
    mock_parent_allow_request.assert_called_once_with(mock_request, mock_view)
    assert result is False


def test_master_api_key_user_rate_throttle__regular_user__not_throttled(
    mocker: MockerFixture,
    admin_user: FFAdminUser,
) -> None:
    # Given
    throttle = MasterAPIKeyUserRateThrottle()

    mock_request = MagicMock(spec=Request)
    mock_request.user = admin_user

    mock_view = MagicMock()

    mock_parent_allow_request = mocker.patch(
        "rest_framework.throttling.UserRateThrottle.allow_request",
        return_value=False,
    )

    # When
    result = throttle.allow_request(mock_request, mock_view)

    # Then
    mock_parent_allow_request.assert_not_called()
    assert result is True


def test_master_api_key_user_rate_throttle__anonymous_user__not_throttled(
    mocker: MockerFixture,
) -> None:
    # Given
    throttle = MasterAPIKeyUserRateThrottle()

    mock_request = MagicMock(spec=Request)
    mock_request.user = None

    mock_view = MagicMock()

    mock_parent_allow_request = mocker.patch(
        "rest_framework.throttling.UserRateThrottle.allow_request",
        return_value=False,
    )

    # When
    result = throttle.allow_request(mock_request, mock_view)

    # Then
    mock_parent_allow_request.assert_not_called()
    assert result is True
