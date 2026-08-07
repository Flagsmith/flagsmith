import base64
import hashlib
import secrets
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth.models import AbstractUser
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.test import APIClient

from oauth2_metadata.constants import FLAGSMITH_CLI_CLIENT_ID


def _pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for S256 PKCE."""
    code_verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


@pytest.fixture()
def oauth_application(admin_user: AbstractUser) -> Application:
    return Application.objects.create(
        name="Test App",
        user=admin_user,
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris="https://example.com/callback",
    )


@pytest.fixture()
def verified_oauth_application(admin_user: AbstractUser) -> Application:
    return Application.objects.create(
        name="Verified App",
        user=admin_user,
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris="https://example.com/callback",
        skip_authorization=True,
    )


@pytest.fixture()
def auth_client(admin_user: AbstractUser) -> APIClient:
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
    url = "/api/v1/oauth/authorize/"

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
    url = "/api/v1/oauth/authorize/"

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

    # When
    response = auth_client.get(
        "/api/v1/oauth/authorize/",
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
    assert "error" in response.json()


def test_post__invalid_client_id__returns_400(
    auth_client: APIClient,
    pkce_pair: tuple[str, str],
    db: None,
) -> None:
    # Given
    _verifier, challenge = pkce_pair
    url = "/api/v1/oauth/authorize/"

    # When
    response = auth_client.post(
        url,
        {
            "allow": True,
            "client_id": "nonexistent-client-id",
            "response_type": "code",
            "redirect_uri": "https://example.com/callback",
            "scope": "mcp",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()


@pytest.mark.parametrize("method", ["get", "post"])
def test_authorize__unauthenticated__returns_401(
    method: str,
    db: None,
) -> None:
    # Given
    client = APIClient()

    # When
    response = getattr(client, method)(
        "/api/v1/oauth/authorize/",
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

    # When
    response = auth_client.post(
        "/api/v1/oauth/authorize/",
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

    # When
    response = auth_client.post(
        "/api/v1/oauth/authorize/",
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

    token_client = APIClient()
    token_response = token_client.post(
        "/o/token/",
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


def test_get__third_party_application_requests_admin_api__returns_invalid_scope(
    auth_client: APIClient,
    oauth_application: Application,
    pkce_pair: tuple[str, str],
) -> None:
    # Given
    _verifier, challenge = pkce_pair

    # When
    response = auth_client.get(
        "/api/v1/oauth/authorize/",
        {
            "client_id": oauth_application.client_id,
            "response_type": "code",
            "redirect_uri": "https://example.com/callback",
            "scope": "admin-api",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "invalid_scope"


def test_get__flagsmith_cli_requests_admin_api__returns_application_info(
    auth_client: APIClient,
    pkce_pair: tuple[str, str],
    db: None,
) -> None:
    # Given
    application = Application.objects.get(client_id=FLAGSMITH_CLI_CLIENT_ID)
    _verifier, challenge = pkce_pair

    # When
    response = auth_client.get(
        "/api/v1/oauth/authorize/",
        {
            "client_id": application.client_id,
            "response_type": "code",
            "redirect_uri": "http://127.0.0.1:53682/callback",
            "scope": "admin-api",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["application"]["client_id"] == FLAGSMITH_CLI_CLIENT_ID
    assert "admin-api" in data["scopes"]
    assert data["is_verified"] is True


# ---------------------------------------------------------------------------
# CIMD integration — OAuthAuthorizeView with HTTPS URL client_ids
# ---------------------------------------------------------------------------

CIMD_CLIENT_ID_URL = "https://cimd.example.com/oauth/metadata"


def _mock_cimd_doc(
    client_id: str = CIMD_CLIENT_ID_URL,
    client_name: str = "CIMD Test App",
    redirect_uris: list[str] | None = None,
) -> dict:
    return {
        "client_id": client_id,
        "client_name": client_name,
        "redirect_uris": redirect_uris or ["https://example.com/callback"],
    }


def test_get__cimd_client_id__resolves_and_returns_application_info(
    auth_client: APIClient,
    pkce_pair: tuple[str, str],
    db: None,
) -> None:
    # Given
    _verifier, challenge = pkce_pair
    doc = _mock_cimd_doc()

    # When
    with (
        patch("oauth2_metadata.cimd._fetch_cimd_document", return_value=doc),
        patch("oauth2_metadata.cimd._is_public_hostname", return_value=True),
        patch("oauth2_metadata.cimd.cache"),
    ):
        response = auth_client.get(
            "/api/v1/oauth/authorize/",
            {
                "client_id": CIMD_CLIENT_ID_URL,
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
    assert data["application"]["name"] == "CIMD Test App"
    assert data["application"]["client_id"] == CIMD_CLIENT_ID_URL
    assert data["is_verified"] is False


def test_get__cimd_client_id_resolution_fails__returns_400(
    auth_client: APIClient,
    pkce_pair: tuple[str, str],
    db: None,
) -> None:
    # Given
    _verifier, challenge = pkce_pair

    # When
    with (
        patch(
            "oauth2_metadata.cimd._fetch_cimd_document",
            side_effect=ValueError("unreachable"),
        ),
        patch("oauth2_metadata.cimd.cache"),
    ):
        response = auth_client.get(
            "/api/v1/oauth/authorize/",
            {
                "client_id": CIMD_CLIENT_ID_URL,
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
    assert data["error"] == "invalid_client"


def test_post__cimd_consent_allow__returns_redirect(
    auth_client: APIClient,
    db: None,
) -> None:
    # Given
    _verifier, challenge = _pkce_pair()
    doc = _mock_cimd_doc()

    # When
    with (
        patch("oauth2_metadata.cimd._fetch_cimd_document", return_value=doc),
        patch("oauth2_metadata.cimd._is_public_hostname", return_value=True),
        patch("oauth2_metadata.cimd.cache"),
    ):
        response = auth_client.post(
            "/api/v1/oauth/authorize/",
            {
                "allow": True,
                "client_id": CIMD_CLIENT_ID_URL,
                "response_type": "code",
                "redirect_uri": "https://example.com/callback",
                "scope": "mcp",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": "cimd-test-state",
            },
            format="json",
        )

    # Then
    assert response.status_code == status.HTTP_200_OK
    redirect_uri = response.json()["redirect_uri"]
    parsed = urlparse(redirect_uri)
    query_params = parse_qs(parsed.query)
    assert "code" in query_params
    assert query_params["state"] == ["cimd-test-state"]


def test_post__cimd_client_id_resolution_fails__returns_400(
    auth_client: APIClient,
    db: None,
) -> None:
    # Given
    _verifier, challenge = _pkce_pair()

    # When
    with (
        patch(
            "oauth2_metadata.cimd._fetch_cimd_document",
            side_effect=ValueError("unreachable"),
        ),
        patch("oauth2_metadata.cimd.cache"),
    ):
        response = auth_client.post(
            "/api/v1/oauth/authorize/",
            {
                "allow": True,
                "client_id": CIMD_CLIENT_ID_URL,
                "response_type": "code",
                "redirect_uri": "https://example.com/callback",
                "scope": "mcp",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
            format="json",
        )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error"] == "invalid_client"
