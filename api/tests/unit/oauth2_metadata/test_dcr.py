from unittest.mock import patch

import pytest
from django.urls import reverse
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.test import APIClient

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
def test_dcr_register__localhost_http__returns_201(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload(
        redirect_uris=["http://localhost:8080/callback"],
    )

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db()
def test_dcr_register__127_0_0_1_http__returns_201(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload(
        redirect_uris=["http://127.0.0.1:3000/callback"],
    )

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_dcr_register__missing_client_name__returns_400(
    api_client: APIClient,
) -> None:
    # Given
    payload = {"redirect_uris": ["https://example.com/callback"]}

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "client_name" in response.json()


def test_dcr_register__missing_redirect_uris__returns_400(
    api_client: APIClient,
) -> None:
    # Given
    payload = {"client_name": "Test"}

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "redirect_uris" in response.json()


def test_dcr_register__empty_redirect_uris__returns_400(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload(redirect_uris=[])

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "redirect_uris" in response.json()


def test_dcr_register__http_redirect_uri__returns_400(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload(
        redirect_uris=["http://example.com/callback"],
    )

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "redirect_uris" in response.json()


def test_dcr_register__wildcard_redirect_uri__returns_400(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload(
        redirect_uris=["https://*.example.com/callback"],
    )

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "redirect_uris" in response.json()


def test_dcr_register__fragment_in_redirect_uri__returns_400(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload(
        redirect_uris=["https://example.com/callback#frag"],
    )

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "redirect_uris" in response.json()


def test_dcr_register__unsupported_grant_type__returns_400(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload(grant_types=["implicit"])

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "grant_types" in response.json()


def test_dcr_register__unsupported_response_type__returns_400(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload(response_types=["token"])

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "response_types" in response.json()


def test_dcr_register__unsupported_auth_method__returns_400(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload(token_endpoint_auth_method="client_secret_basic")

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "token_endpoint_auth_method" in response.json()


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
def test_dcr_register__creates_public_application_in_database(
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


def test_dcr_register__too_many_redirect_uris__returns_400(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload(
        redirect_uris=[f"https://example.com/cb{i}" for i in range(6)],
    )

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "redirect_uris" in response.json()


def test_dcr_register__html_in_client_name__returns_400(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload(client_name="<script>alert(1)</script>")

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "client_name" in response.json()


@pytest.mark.django_db()
def test_dcr_register__valid_client_name_with_special_chars__returns_201(
    api_client: APIClient,
) -> None:
    # Given — parentheses, dots, hyphens are allowed
    payload = _valid_payload(client_name="Claude Desktop (v2.1-beta)")

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["client_name"] == "Claude Desktop (v2.1-beta)"


def test_dcr_register__get_request__returns_405(
    api_client: APIClient,
) -> None:
    # When
    response = api_client.get(DCR_URL)

    # Then
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db()
def test_dcr_register__rate_limited__returns_429(
    api_client: APIClient,
) -> None:
    # Given
    payload = _valid_payload()

    with patch(
        "rest_framework.throttling.ScopedRateThrottle.allow_request",
        return_value=False,
    ), patch(
        "rest_framework.throttling.ScopedRateThrottle.wait",
        return_value=60.0,
    ):
        # When
        response = api_client.post(DCR_URL, data=payload, format="json")

        # Then
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
