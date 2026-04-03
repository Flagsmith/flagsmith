import base64
import hashlib
import secrets
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.test import APIClient

AUTHORIZE_URL = "oauth-authorize"

User = get_user_model()


def _pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for S256 PKCE."""
    code_verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


@pytest.fixture()
def oauth_application(admin_user: User) -> Application:  # type: ignore[valid-type]
    return Application.objects.create(  # type: ignore[no-any-return]
        name="Test App",
        user=admin_user,
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris="https://example.com/callback",
    )


@pytest.fixture()
def verified_oauth_application(admin_user: User) -> Application:  # type: ignore[valid-type]
    return Application.objects.create(  # type: ignore[no-any-return]
        name="Verified App",
        user=admin_user,
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris="https://example.com/callback",
        skip_authorization=True,
    )


@pytest.fixture()
def auth_client(admin_user: User) -> APIClient:  # type: ignore[valid-type]
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture()
def pkce_pair() -> tuple[str, str]:
    return _pkce_pair()


def test_get__valid_params__returns_application_info(
    auth_client: APIClient,
    oauth_application: Application,
    pkce_pair: tuple[str, str],
) -> None:
    # Given
    _verifier, challenge = pkce_pair
    url = reverse(AUTHORIZE_URL)

    # When
    response = auth_client.get(
        url,
        {
            "client_id": oauth_application.client_id,
            "response_type": "code",
            "redirect_uri": "https://example.com/callback",
            "scope": "mcp",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["application"]["name"] == "Test App"
    assert data["application"]["client_id"] == oauth_application.client_id
    assert "mcp" in data["scopes"]
    assert data["redirect_uri"] == "https://example.com/callback"
    assert data["is_verified"] is False


def test_get__verified_application__returns_is_verified_true(
    auth_client: APIClient,
    verified_oauth_application: Application,
    pkce_pair: tuple[str, str],
) -> None:
    # Given
    _verifier, challenge = pkce_pair
    url = reverse(AUTHORIZE_URL)

    # When
    response = auth_client.get(
        url,
        {
            "client_id": verified_oauth_application.client_id,
            "response_type": "code",
            "redirect_uri": "https://example.com/callback",
            "scope": "mcp",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_verified"] is True


def test_get__invalid_client_id__returns_400(
    auth_client: APIClient,
    pkce_pair: tuple[str, str],
    db: None,
) -> None:
    # Given
    _verifier, challenge = pkce_pair
    url = reverse(AUTHORIZE_URL)

    # When
    response = auth_client.get(
        url,
        {
            "client_id": "nonexistent-client-id",
            "response_type": "code",
            "redirect_uri": "https://example.com/callback",
            "scope": "mcp",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "error" in data


@pytest.mark.parametrize("method", ["get", "post"])
def test__unauthenticated__returns_401(
    method: str,
    db: None,
) -> None:
    # Given
    client = APIClient()
    url = reverse(AUTHORIZE_URL)

    # When
    response = getattr(client, method)(
        url,
        {"client_id": "some-id", "response_type": "code"},
    )

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(
    "allow, expected_params",
    [
        (True, {"state": ["test-state"]}),
        (False, {"error": ["access_denied"], "state": ["test-state"]}),
    ],
    ids=["allow", "deny"],
)
def test_post__consent_decision__returns_redirect(
    auth_client: APIClient,
    oauth_application: Application,
    pkce_pair: tuple[str, str],
    allow: bool,
    expected_params: dict[str, list[str]],
) -> None:
    # Given
    _verifier, challenge = pkce_pair
    url = reverse(AUTHORIZE_URL)

    # When
    response = auth_client.post(
        url,
        {
            "allow": allow,
            "client_id": oauth_application.client_id,
            "response_type": "code",
            "redirect_uri": "https://example.com/callback",
            "scope": "mcp",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "test-state",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    redirect_uri = response.json()["redirect_uri"]
    parsed = urlparse(redirect_uri)
    query_params = parse_qs(parsed.query)
    for key, value in expected_params.items():
        assert query_params[key] == value


def test_post__pkce_params_preserved__code_exchangeable(
    auth_client: APIClient,
    oauth_application: Application,
) -> None:
    # Given
    code_verifier, code_challenge = _pkce_pair()
    authorize_url = reverse(AUTHORIZE_URL)

    # When
    response = auth_client.post(
        authorize_url,
        {
            "allow": True,
            "client_id": oauth_application.client_id,
            "response_type": "code",
            "redirect_uri": "https://example.com/callback",
            "scope": "mcp",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    redirect_uri = response.json()["redirect_uri"]
    parsed = urlparse(redirect_uri)
    query_params = parse_qs(parsed.query)
    code = query_params["code"][0]

    token_url = reverse("oauth2_provider:token")
    token_client = APIClient()
    token_response = token_client.post(
        token_url,
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "https://example.com/callback",
            "client_id": oauth_application.client_id,
            "code_verifier": code_verifier,
        },
    )

    # Then
    assert token_response.status_code == status.HTTP_200_OK
    token_data = token_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "Bearer"
