from unittest import mock

import pytest
from django.core.exceptions import PermissionDenied
from django.test import override_settings

from core.middleware.admin import AdminWhitelistMiddleware

allowed_ip_address = "10.0.0.1"
not_allowed_ip_address = "11.0.0.1"


@override_settings(ALLOWED_ADMIN_IP_ADDRESSES=[allowed_ip_address])
def test_admin_whitelist_middleware_raises_permission_denied_for_admin_pages_if_ip_not_allowed():
    # Given
    mock_get_response = mock.MagicMock()

    mock_request = mock.MagicMock()
    mock_request.path = "/admin/login"
    mock_request.META = {"REMOTE_ADDR": not_allowed_ip_address}

    middleware = AdminWhitelistMiddleware(mock_get_response)

    # When
    with pytest.raises(PermissionDenied):
        middleware(mock_request)

    # Then - exception raised


@override_settings(ALLOWED_ADMIN_IP_ADDRESSES=[allowed_ip_address])
def test_admin_whitelist_middleware_returns_get_response_for_admin_pages_if_ip_allowed():
    # Given
    mock_get_response = mock.MagicMock()
    mock_get_response_return = mock.MagicMock()
    mock_get_response.return_value = mock_get_response_return

    mock_request = mock.MagicMock()
    mock_request.path = "/admin/login"
    mock_request.META = {"REMOTE_ADDR": allowed_ip_address}

    middleware = AdminWhitelistMiddleware(mock_get_response)

    # When
    response = middleware(mock_request)

    # Then
    mock_get_response.assert_called_with(mock_request)
    assert response == mock_get_response_return


@override_settings(ALLOWED_ADMIN_IP_ADDRESSES=[allowed_ip_address])
def test_admin_whitelist_middleware_returns_get_response_for_non_admin_request_if_ip_not_allowed():
    # Given
    mock_get_response = mock.MagicMock()
    mock_get_response_return = mock.MagicMock()
    mock_get_response.return_value = mock_get_response_return

    mock_request = mock.MagicMock()
    mock_request.path = "/api/v1/flags"
    mock_request.META = {"REMOTE_ADDR": not_allowed_ip_address}

    middleware = AdminWhitelistMiddleware(mock_get_response)

    # When
    response = middleware(mock_request)

    # Then
    mock_get_response.assert_called_with(mock_request)
    assert response == mock_get_response_return
