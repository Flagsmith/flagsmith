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
    setattr(throttle, "num_requests", 1)
    setattr(throttle, "duration", 60)  # 1 minute
    user = APIKeyUser(admin_master_api_key_object)

    mock_request = MagicMock(spec=Request)
    mock_request.user = user

    mock_view = MagicMock()

    throttle.allow_request(mock_request, mock_view)

    # When
    result = throttle.allow_request(mock_request, mock_view)

    # Then
    assert result is False


def test_master_api_key_user_rate_throttle__regular_user__not_throttled(
    mocker: MockerFixture,
    admin_user: FFAdminUser,
) -> None:
    # Given
    throttle = MasterAPIKeyUserRateThrottle()
    setattr(throttle, "num_requests", 1)
    setattr(throttle, "duration", 60)  # 1 minute

    mock_request = MagicMock(spec=Request)
    mock_request.user = admin_user

    mock_view = MagicMock()

    throttle.allow_request(mock_request, mock_view)

    # When
    result = throttle.allow_request(mock_request, mock_view)

    # Then
    assert result is True


def test_master_api_key_user_rate_throttle__anonymous_user__not_throttled(
    mocker: MockerFixture,
) -> None:
    # Given
    throttle = MasterAPIKeyUserRateThrottle()
    setattr(throttle, "num_requests", 1)
    setattr(throttle, "duration", 60)  # 1 minute

    mock_request = MagicMock(spec=Request)
    mock_request.user = None

    mock_view = MagicMock()

    throttle.allow_request(mock_request, mock_view)

    # When
    result = throttle.allow_request(mock_request, mock_view)

    # Then
    assert result is True
