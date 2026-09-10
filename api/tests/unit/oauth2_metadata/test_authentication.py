from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from django.utils import timezone
from oauth2_provider.models import AccessToken, Application
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from oauth2_metadata.authentication import OAuth2BearerTokenAuthentication
from users.models import FFAdminUser


@pytest.mark.parametrize(
    "auth_header",
    [
        "",
        "Token some-token",
        "Basic dXNlcjpwYXNz",
        "Api-Key master-api-key",
    ],
)
def test_authenticate__non_bearer_header__returns_none(
    auth_header: str,
) -> None:
    # Given
    factory = APIRequestFactory()
    request = Request(factory.get("/", HTTP_AUTHORIZATION=auth_header))
    auth = OAuth2BearerTokenAuthentication()

    # When
    result = auth.authenticate(request)

    # Then
    assert result is None


def test_authenticate__bearer_header__delegates_to_dot(
    mocker: MagicMock,
) -> None:
    # Given
    mock_user = MagicMock()
    mocker.patch(
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication.authenticate",
        return_value=(mock_user, "test-token"),
    )
    request = Request(
        APIRequestFactory().get("/", HTTP_AUTHORIZATION="Bearer test-token")
    )
    auth = OAuth2BearerTokenAuthentication()

    # When
    result = auth.authenticate(request)

    # Then
    assert result == (mock_user, "test-token")


def test_authenticate__token_bound_to_mcp_resource__authenticates_user(
    admin_user: FFAdminUser,
) -> None:
    # Given
    app = Application.objects.create(
        name="MCP client",
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris="https://example.com/callback",
    )
    AccessToken.objects.create(
        user=admin_user,
        application=app,
        token="mcp-token",
        scope="mcp",
        expires=timezone.now() + timedelta(hours=1),
        resource=["https://mcp.example.com/"],
    )
    request = Request(
        APIRequestFactory().get(
            "/api/v1/organisations/", HTTP_AUTHORIZATION="Bearer mcp-token"
        )
    )
    auth = OAuth2BearerTokenAuthentication()

    # When
    result = auth.authenticate(request)

    # Then
    assert result is not None
    assert result[0] == admin_user
