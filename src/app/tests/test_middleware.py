from unittest import mock

import pytest
from django.core.exceptions import PermissionDenied

from app.middleware import AdminWhitelistMiddleware


@mock.patch("app.middleware.settings")
def test_admin_whitelist_middleware_raises_permission_denied_for_admin_pages_if_ip_not_allowed(
    mock_settings,
):
    # Given
    allowed_ip_address = "10.0.0.1"
    not_allowed_ip_address = "11.0.0.1"

    mock_get_response = mock.MagicMock()

    mock_request = mock.MagicMock()
    mock_request.path = "/admin/login"
    mock_request.META = {"REMOTE_ADDR": not_allowed_ip_address}

    mock_settings.ALLOWED_ADMIN_IP_ADDRESSES = [allowed_ip_address]

    middleware = AdminWhitelistMiddleware(mock_get_response)

    # When
    with pytest.raises(PermissionDenied):
        middleware(mock_request)

    # Then - exception raised


@mock.patch("app.middleware.settings")
def test_admin_whitelist_middleware_returns_get_response_for_admin_pages_if_ip_allowed(
    mock_settings,
):
    # Given
    allowed_ip_address = "10.0.0.1"

    mock_get_response = mock.MagicMock()
    mock_get_response_return = mock.MagicMock()
    mock_get_response.return_value = mock_get_response_return

    mock_request = mock.MagicMock()
    mock_request.path = "/admin/login"
    mock_request.META = {"REMOTE_ADDR": allowed_ip_address}

    mock_settings.ALLOWED_ADMIN_IP_ADDRESSES = [allowed_ip_address]

    middleware = AdminWhitelistMiddleware(mock_get_response)

    # When
    response = middleware(mock_request)

    # Then
    mock_get_response.assert_called_with(mock_request)
    assert response == mock_get_response_return


@mock.patch("app.middleware.settings")
def test_admin_whitelist_middleware_returns_get_response_for_non_admin_request_if_ip_not_allowed(
    mock_settings,
):
    # Given
    allowed_ip_address = "10.0.0.1"
    not_allowed_ip_address = "11.0.0.1"

    mock_get_response = mock.MagicMock()
    mock_get_response_return = mock.MagicMock()
    mock_get_response.return_value = mock_get_response_return

    mock_request = mock.MagicMock()
    mock_request.path = "/api/v1/flags"
    mock_request.META = {"REMOTE_ADDR": not_allowed_ip_address}

    mock_settings.ALLOWED_ADMIN_IP_ADDRESSES = [allowed_ip_address]

    middleware = AdminWhitelistMiddleware(mock_get_response)

    # When
    response = middleware(mock_request)

    # Then
    mock_get_response.assert_called_with(mock_request)
    assert response == mock_get_response_return
