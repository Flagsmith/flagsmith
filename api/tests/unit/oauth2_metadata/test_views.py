import pytest
from django.test import Client
from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper
from rest_framework import status

METADATA_URL = "oauth-authorization-server-metadata"


@pytest.fixture()
def client() -> Client:
    return Client()


def test_metadata_endpoint__unauthenticated__returns_200_with_rfc8414_json(
    client: Client,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.FLAGSMITH_API_URL = "https://api.flagsmith.com"
    settings.FLAGSMITH_FRONTEND_URL = "https://app.flagsmith.com"

    # When
    response = client.get(reverse(METADATA_URL))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"] == "application/json"

    data = response.json()
    assert data["issuer"] == "https://api.flagsmith.com"
    assert data["authorization_endpoint"] == "https://app.flagsmith.com/oauth/authorize/"
    assert data["token_endpoint"] == "https://api.flagsmith.com/o/token/"
    assert data["registration_endpoint"] == "https://api.flagsmith.com/o/register/"
    assert data["revocation_endpoint"] == "https://api.flagsmith.com/o/revoke_token/"
    assert data["introspection_endpoint"] == "https://api.flagsmith.com/o/introspect/"
    assert data["response_types_supported"] == ["code"]
    assert data["grant_types_supported"] == ["authorization_code", "refresh_token"]
    assert data["code_challenge_methods_supported"] == ["S256"]
    assert "none" in data["token_endpoint_auth_methods_supported"]
    assert data["introspection_endpoint_auth_methods_supported"] == ["none"]


def test_metadata_endpoint__custom_urls__endpoints_derived_from_settings(
    client: Client,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.FLAGSMITH_API_URL = "https://custom-api.example.com"
    settings.FLAGSMITH_FRONTEND_URL = "https://custom-app.example.com"

    # When
    response = client.get(reverse(METADATA_URL))

    # Then
    data = response.json()
    assert data["issuer"] == "https://custom-api.example.com"
    assert data["authorization_endpoint"].startswith("https://custom-app.example.com/")
    assert data["token_endpoint"].startswith("https://custom-api.example.com/")
    assert data["registration_endpoint"].startswith("https://custom-api.example.com/")
    assert data["revocation_endpoint"].startswith("https://custom-api.example.com/")
    assert data["introspection_endpoint"].startswith("https://custom-api.example.com/")


def test_metadata_endpoint__trailing_slash_in_url__no_double_slash(
    client: Client,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.FLAGSMITH_API_URL = "https://api.flagsmith.com/"
    settings.FLAGSMITH_FRONTEND_URL = "https://app.flagsmith.com/"

    # When
    response = client.get(reverse(METADATA_URL))

    # Then
    data = response.json()
    assert "//" not in data["token_endpoint"].split("://")[1]
    assert "//" not in data["authorization_endpoint"].split("://")[1]


def test_metadata_endpoint__scopes__reflect_oauth2_provider_settings(
    client: Client,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.OAUTH2_PROVIDER = {
        **settings.OAUTH2_PROVIDER,
        "SCOPES": {"mcp": "MCP access", "read": "Read access"},
    }

    # When
    response = client.get(reverse(METADATA_URL))

    # Then
    data = response.json()
    assert set(data["scopes_supported"]) == {"mcp", "read"}


def test_metadata_endpoint__post_request__returns_405(
    client: Client,
) -> None:
    # When
    response = client.post(reverse(METADATA_URL))

    # Then
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
