"""Tests for CIMDTokenView — token endpoint with CIMD client_id support."""

import base64
import hashlib
import secrets
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AbstractUser
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.test import APIClient

CIMD_CLIENT_ID_URL = "https://cimd.example.com/oauth/metadata"


def _pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for S256 PKCE."""
    code_verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


def _mock_cimd_doc(
    client_id: str = CIMD_CLIENT_ID_URL,
    client_name: str = "CIMD Token App",
    redirect_uris: list[str] | None = None,
) -> dict:
    return {
        "client_id": client_id,
        "client_name": client_name,
        "redirect_uris": redirect_uris or ["https://example.com/callback"],
    }


@pytest.fixture()
def auth_client(admin_user: AbstractUser) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


def _obtain_auth_code(
    auth_client: APIClient,
    client_id: str,
    code_challenge: str,
) -> str:
    """Use the authorize endpoint to obtain an authorization code."""
    response = auth_client.post(
        "/api/v1/oauth/authorize/",
        {
            "allow": True,
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": "https://example.com/callback",
            "scope": "mcp",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    from urllib.parse import parse_qs, urlparse

    redirect_uri = response.json()["redirect_uri"]
    query_params = parse_qs(urlparse(redirect_uri).query)
    return query_params["code"][0]


def test_token__cimd_resolution_fails__returns_400(
    db: None,
) -> None:
    # Given
    token_client = APIClient()

    # When
    with (
        patch(
            "oauth2_metadata.cimd._fetch_cimd_document",
            side_effect=ValueError("unreachable"),
        ),
        patch("oauth2_metadata.cimd.cache"),
    ):
        response = token_client.post(
            "/o/token/",
            {
                "grant_type": "authorization_code",
                "code": "dummy-code",
                "redirect_uri": "https://example.com/callback",
                "client_id": CIMD_CLIENT_ID_URL,
                "code_verifier": "dummy-verifier",
            },
        )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error"] == "invalid_client"


def test_token__cimd_full_flow__issues_token(
    auth_client: APIClient,
    db: None,
) -> None:
    # Given — obtain an auth code through the authorize endpoint.
    code_verifier, code_challenge = _pkce_pair()
    doc = _mock_cimd_doc()

    with (
        patch("oauth2_metadata.cimd._fetch_cimd_document", return_value=doc),
        patch("oauth2_metadata.cimd._is_public_hostname", return_value=True),
        patch("oauth2_metadata.cimd.cache"),
    ):
        code = _obtain_auth_code(auth_client, CIMD_CLIENT_ID_URL, code_challenge)

    # When — exchange the code for a token at the CIMD-aware token endpoint.
    token_client = APIClient()
    with (
        patch("oauth2_metadata.cimd._fetch_cimd_document", return_value=doc),
        patch("oauth2_metadata.cimd._is_public_hostname", return_value=True),
        patch("oauth2_metadata.cimd.cache"),
    ):
        response = token_client.post(
            "/o/token/",
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "https://example.com/callback",
                "client_id": CIMD_CLIENT_ID_URL,
                "code_verifier": code_verifier,
            },
        )

    # Then
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "Bearer"


def test_token__non_cimd_client_id__still_works(
    auth_client: APIClient,
    admin_user: AbstractUser,
    db: None,
) -> None:
    """DCR-registered (opaque) client_ids still work through CIMDTokenView."""
    # Given — create a regular application and obtain an auth code.
    application = Application.objects.create(
        name="Regular DCR App",
        user=admin_user,
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris="https://example.com/callback",
    )
    code_verifier, code_challenge = _pkce_pair()
    code = _obtain_auth_code(auth_client, application.client_id, code_challenge)

    # When — exchange the code at the token endpoint (no CIMD resolution needed).
    token_client = APIClient()
    response = token_client.post(
        "/o/token/",
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "https://example.com/callback",
            "client_id": application.client_id,
            "code_verifier": code_verifier,
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "Bearer"
