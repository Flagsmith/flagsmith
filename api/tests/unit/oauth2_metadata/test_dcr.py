from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.test import APIClient

from oauth2_metadata.services import validate_redirect_uri

DCR_URL = reverse("oauth2-dcr-register")


@pytest.fixture()
def api_client() -> APIClient:
    return APIClient()


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "client_name": "Test MCP Client",
        "redirect_uris": ["https://example.com/callback"],
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db()
def test_dcr_register__valid_request__returns_201_with_client_id(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload()

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["client_id"]
    assert data["client_name"] == "Test MCP Client"
    assert data["redirect_uris"] == ["https://example.com/callback"]
    assert data["grant_types"] == ["authorization_code", "refresh_token"]
    assert data["response_types"] == ["code"]
    assert data["token_endpoint_auth_method"] == "none"
    assert isinstance(data["client_id_issued_at"], int)


@pytest.mark.django_db()
@pytest.mark.parametrize(
    "redirect_uri",
    [
        "http://localhost:8080/callback",
        "http://127.0.0.1:3000/callback",
        "http://[::1]:3000/callback",
        "https://example.com/callback",
    ],
    ids=["localhost", "127.0.0.1", "::1", "https"],
)
def test_dcr_register__valid_redirect_uri__returns_201(
    api_client: APIClient,
    redirect_uri: str,
) -> None:
    # Given
    payload = _valid_payload(redirect_uris=[redirect_uri])

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db()
@pytest.mark.parametrize(
    "client_name",
    [
        "Claude Desktop (v2.1-beta)",
        "My_App.test",
        "Simple",
    ],
    ids=["special-chars", "underscores-dots", "simple"],
)
def test_dcr_register__valid_client_name__returns_201(
    api_client: APIClient,
    client_name: str,
) -> None:
    # Given
    payload = _valid_payload(client_name=client_name)

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["client_name"] == client_name


@pytest.mark.django_db()
def test_dcr_register__defaults_applied__returns_expected_defaults(
    api_client: APIClient,
) -> None:
    # Given - only required fields
    payload = _valid_payload()

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    data = response.json()
    assert data["grant_types"] == ["authorization_code", "refresh_token"]
    assert data["response_types"] == ["code"]
    assert data["token_endpoint_auth_method"] == "none"


@pytest.mark.django_db()
def test_dcr_register__valid_request__creates_public_application_in_database(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload()

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    client_id = response.json()["client_id"]
    application = Application.objects.get(client_id=client_id)
    assert application.client_type == Application.CLIENT_PUBLIC
    assert application.authorization_grant_type == Application.GRANT_AUTHORIZATION_CODE
    assert application.name == "Test MCP Client"
    assert "https://example.com/callback" in application.redirect_uris
    assert application.user is None
    assert application.skip_authorization is False


@pytest.mark.parametrize(
    ("redirect_uris", "expected_fragment"),
    [
        (["http://example.com/callback"], "HTTPS"),
        (["https://example.com/callback#frag"], "Fragment"),
        (["https://*.example.com/callback"], ""),  # Rejected by URLField
        ([], ""),  # Empty list
        ([f"https://example.com/cb{i}" for i in range(6)], ""),  # Too many
    ],
    ids=["http-non-localhost", "fragment", "wildcard", "empty-list", "too-many"],
)
def test_dcr_register__invalid_redirect_uris__returns_rfc7591_error(
    api_client: APIClient,
    redirect_uris: list[str],
    expected_fragment: str,
) -> None:
    # Given
    payload = _valid_payload(redirect_uris=redirect_uris)

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error"] == "invalid_redirect_uri"
    assert "error_description" in data
    if expected_fragment:
        assert expected_fragment in data["error_description"]


@pytest.mark.parametrize(
    ("overrides", "expected_fragment"),
    [
        ({"client_name": "<script>alert(1)</script>"}, ""),
        ({"client_name": "   "}, "blank"),
        ({"grant_types": ["implicit"]}, "grant type"),
        ({"response_types": ["token"]}, "response type"),
        ({"token_endpoint_auth_method": "client_secret_basic"}, "public clients"),
    ],
    ids=["xss-client-name", "blank-client-name", "bad-grant-type", "bad-response-type", "bad-auth-method"],
)
def test_dcr_register__invalid_client_metadata__returns_rfc7591_error(
    api_client: APIClient,
    overrides: dict[str, object],
    expected_fragment: str,
) -> None:
    # Given
    payload = _valid_payload(**overrides)

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error"] == "invalid_client_metadata"
    assert "error_description" in data
    if expected_fragment:
        assert expected_fragment in data["error_description"].lower()


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        (
            {"redirect_uris": ["https://example.com/callback"]},
            "invalid_client_metadata",
        ),
        (
            {"client_name": "Test"},
            "invalid_redirect_uri",
        ),
    ],
    ids=["missing-client-name", "missing-redirect-uris"],
)
def test_dcr_register__missing_required_field__returns_rfc7591_error(
    api_client: APIClient,
    payload: dict[str, object],
    expected_error: str,
) -> None:
    # Given / When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error"] == expected_error
    assert "error_description" in data


def test_dcr_register__get_request__returns_405(
    api_client: APIClient,
) -> None:
    # Given / When
    response = api_client.get(DCR_URL)

    # Then
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db()
def test_dcr_register__rate_limited__returns_429(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload()

    with (
        patch(
            "rest_framework.throttling.ScopedRateThrottle.allow_request",
            return_value=False,
        ),
        patch(
            "rest_framework.throttling.ScopedRateThrottle.wait",
            return_value=60.0,
        ),
    ):
        # When
        response = api_client.post(DCR_URL, data=payload, format="json")

        # Then
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.parametrize(
    ("uri", "expected_message"),
    [
        ("not-a-uri", "Invalid URI"),
        ("https://*.example.com/callback", "Wildcards"),
    ],
    ids=["invalid-uri", "wildcard"],
)
def test_validate_redirect_uri__invalid_input__raises_validation_error(
    uri: str,
    expected_message: str,
) -> None:
    # Given / When
    # Then
    with pytest.raises(ValidationError, match=expected_message):
        validate_redirect_uri(uri)
