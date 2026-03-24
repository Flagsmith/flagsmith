from unittest import mock

import pytest
from django.core.exceptions import PermissionDenied
from django.test import override_settings

from core.middleware.admin import AdminWhitelistMiddleware

allowed_ip_address = "10.0.0.1"
not_allowed_ip_address = "11.0.0.1"


@override_settings(ALLOWED_ADMIN_IP_ADDRESSES=[allowed_ip_address])
def test_admin_whitelist_middleware__ip_not_allowed_on_admin_page__raises_permission_denied():  # type: ignore[no-untyped-def]  # noqa: E501
    # Given
    mock_get_response = mock.MagicMock()

    mock_request = mock.MagicMock()
    mock_request.path = "/admin/login"
    mock_request.META = {"REMOTE_ADDR": not_allowed_ip_address}

    middleware = AdminWhitelistMiddleware(mock_get_response)  # type: ignore[no-untyped-call]

    # When / Then
    with pytest.raises(PermissionDenied):
        middleware(mock_request)


@override_settings(ALLOWED_ADMIN_IP_ADDRESSES=[allowed_ip_address])
def test_admin_whitelist_middleware__ip_allowed_on_admin_page__returns_response():  # type: ignore[no-untyped-def]
    # Given
    mock_get_response = mock.MagicMock()
    mock_get_response_return = mock.MagicMock()
    mock_get_response.return_value = mock_get_response_return

    mock_request = mock.MagicMock()
    mock_request.path = "/admin/login"
    mock_request.META = {"REMOTE_ADDR": allowed_ip_address}

    middleware = AdminWhitelistMiddleware(mock_get_response)  # type: ignore[no-untyped-call]

    # When
    response = middleware(mock_request)

    # Then
    mock_get_response.assert_called_with(mock_request)
    assert response == mock_get_response_return


@override_settings(ALLOWED_ADMIN_IP_ADDRESSES=[allowed_ip_address])
def test_admin_whitelist_middleware__ip_not_allowed_on_non_admin_page__returns_response():  # type: ignore[no-untyped-def]
    # Given
    mock_get_response = mock.MagicMock()
    mock_get_response_return = mock.MagicMock()
    mock_get_response.return_value = mock_get_response_return

    mock_request = mock.MagicMock()
    mock_request.path = "/api/v1/flags"
    mock_request.META = {"REMOTE_ADDR": not_allowed_ip_address}

    middleware = AdminWhitelistMiddleware(mock_get_response)  # type: ignore[no-untyped-call]

    # When
    response = middleware(mock_request)

    # Then
    mock_get_response.assert_called_with(mock_request)
    assert response == mock_get_response_return
