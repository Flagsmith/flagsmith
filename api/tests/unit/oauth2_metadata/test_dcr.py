from unittest.mock import patch

import pytest
from common.test_tools import AssertMetricFixture
from django.urls import reverse
from oauth2_provider.models import Application
from pytest_structlog import StructuredLogCapture
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
    assert "client_secret" not in data
    assert "client_secret_expires_at" not in data


@pytest.mark.django_db()
@pytest.mark.parametrize(
    "redirect_uri",
    [
        "http://localhost:8080/callback",
        "http://127.0.0.1:3000/callback",
        "http://[::1]:3000/callback",
        "https://example.com/callback",
        "claude://oauth/callback",
        "com.example.app:/oauth2redirect",
    ],
    ids=["localhost", "127.0.0.1", "::1", "https", "custom-scheme", "reverse-domain"],
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
        (["https://*.example.com/callback"], "Wildcards"),
        (["example.com/callback"], "Invalid URI"),
        (["javascript:alert(1)"], "not permitted"),
        (["data:text/html,x"], "not permitted"),
        ([], "at least 1"),
        ([f"https://example.com/cb{i}" for i in range(6)], "no more than 5"),
    ],
    ids=[
        "http-non-localhost",
        "fragment",
        "wildcard",
        "scheme-less",
        "javascript-scheme",
        "data-scheme",
        "empty-list",
        "too-many",
    ],
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
    assert expected_fragment.lower() in data["error_description"].lower()


@pytest.mark.django_db()
@pytest.mark.parametrize(
    "auth_method",
    ["client_secret_basic", "client_secret_post"],
)
def test_dcr_register__confidential_client__returns_201_with_secret(
    api_client: APIClient,
    auth_method: str,
) -> None:
    # Given
    payload = _valid_payload(token_endpoint_auth_method=auth_method)

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["token_endpoint_auth_method"] == auth_method
    assert data["client_secret"]
    assert data["client_secret_expires_at"] == 0

    application = Application.objects.get(client_id=data["client_id"])
    assert application.client_type == Application.CLIENT_CONFIDENTIAL
    # The secret is hashed at rest; only the response carries the plaintext.
    assert application.client_secret != data["client_secret"]


@pytest.mark.django_db()
def test_dcr_register__valid_request__increments_registration_metric(
    api_client: APIClient,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given / When
    api_client.post(DCR_URL, data=_valid_payload(), format="json")

    # Then
    assert_metric(
        name="flagsmith_oauth2_dcr_registrations_total",
        labels={"token_endpoint_auth_method": "none", "outcome": "registered"},
        value=1,
    )


def test_dcr_register__invalid_auth_method__increments_rejection_metric(
    api_client: APIClient,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given / When - an unsupported method is collapsed to "other".
    api_client.post(
        DCR_URL,
        data=_valid_payload(token_endpoint_auth_method="private_key_jwt"),
        format="json",
    )

    # Then
    assert_metric(
        name="flagsmith_oauth2_dcr_registrations_total",
        labels={"token_endpoint_auth_method": "other", "outcome": "rejected"},
        value=1,
    )


@pytest.mark.parametrize(
    "invalid_uri",
    ["javascript:alert(1)", ""],
    ids=["policy-error", "child-field-error"],
)
def test_dcr_register__invalid_redirect_uri_after_valid_one__returns_rfc7591_error(
    api_client: APIClient,
    invalid_uri: object,
) -> None:
    # Given - the invalid URI is not at index 0, so field errors are keyed
    # by list index rather than returned as a flat list.
    payload = _valid_payload(
        redirect_uris=["https://example.com/callback", invalid_uri]
    )

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error"] == "invalid_redirect_uri"
    assert "ErrorDetail" not in data["error_description"]


@pytest.mark.parametrize(
    ("overrides", "expected_fragment"),
    [
        ({"client_name": "<script>alert(1)</script>"}, "letters"),
        ({"grant_types": ["implicit"]}, "grant type"),
        ({"response_types": ["token"]}, "response type"),
        ({"token_endpoint_auth_method": "private_key_jwt"}, "not a valid choice"),
    ],
    ids=[
        "xss-client-name",
        "bad-grant-type",
        "bad-response-type",
        "bad-auth-method",
    ],
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
    assert expected_fragment.lower() in data["error_description"].lower()


@pytest.mark.django_db()
@pytest.mark.parametrize(
    "payload",
    [
        {"redirect_uris": ["https://example.com/callback"]},
        {"client_name": None, "redirect_uris": ["https://example.com/callback"]},
        {"client_name": "", "redirect_uris": ["https://example.com/callback"]},
        {"client_name": "   ", "redirect_uris": ["https://example.com/callback"]},
    ],
    ids=["absent", "null", "blank", "whitespace-only"],
)
def test_dcr_register__no_client_name__returns_201_with_default_name(
    api_client: APIClient,
    payload: dict[str, object],
) -> None:
    # Given - client_name is optional per RFC 7591 section 2; null and
    # blank values are treated the same as an absent one.

    # When
    response = api_client.post(DCR_URL, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["client_name"] == "MCP client"


def test_dcr_register__missing_redirect_uris__returns_rfc7591_error(
    api_client: APIClient,
) -> None:
    # Given / When
    response = api_client.post(DCR_URL, data={"client_name": "Test"}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error"] == "invalid_redirect_uri"
    assert "error_description" in data


def test_dcr_register__invalid_request__logs_rejection(
    api_client: APIClient,
    log: StructuredLogCapture,
) -> None:
    # Given
    payload = _valid_payload(
        client_name="Claude Desktop",
        redirect_uris=["https://example.com/callback", "javascript:alert(1)"],
    )

    # When
    api_client.post(
        DCR_URL,
        data=payload,
        format="json",
        HTTP_USER_AGENT="Claude-Desktop/1.0",
    )

    # Then
    assert log.events == [
        {
            "level": "error",
            "event": "registration.rejected",
            "error": "invalid_redirect_uri",
            "error_description": (
                "Scheme is not permitted in redirect URIs: javascript:alert(1)"
            ),
            "client__name": "Claude Desktop",
            "redirect_uris": [
                "https://example.com/callback",
                "javascript:alert(1)",
            ],
            "user_agent": "Claude-Desktop/1.0",
        }
    ]


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
