"""Tests for Client ID Metadata Document (CIMD) resolution."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from common.test_tools import AssertMetricFixture
from django.test import Client
from django.urls import reverse
from oauth2_provider.models import Application
from pytest_structlog import StructuredLogCapture
from rest_framework import status

METADATA_URL = "oauth-authorization-server-metadata"


@pytest.fixture()
def client() -> Client:
    return Client()


# ---------------------------------------------------------------------------
# Metadata endpoint
# ---------------------------------------------------------------------------


def test_metadata_endpoint__get__advertises_cimd_support(
    client: Client,
    settings: "SettingsWrapper",  # noqa: F821
) -> None:
    # Given
    settings.FLAGSMITH_API_URL = "https://api.flagsmith.com"
    settings.FLAGSMITH_FRONTEND_URL = "https://app.flagsmith.com"

    # When
    response = client.get(reverse(METADATA_URL))

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["client_id_metadata_document_supported"] is True


# ---------------------------------------------------------------------------
# cimd module: is_cimd_client_id
# ---------------------------------------------------------------------------


def test_is_cimd_client_id__https_url__returns_true() -> None:
    from oauth2_metadata.cimd import is_cimd_client_id

    # Given
    client_id = "https://claude.ai/oauth/metadata"

    # When / Then
    assert is_cimd_client_id(client_id) is True


def test_is_cimd_client_id__opaque_id__returns_false() -> None:
    from oauth2_metadata.cimd import is_cimd_client_id

    # Given
    client_id = "abc123-client-id"

    # When / Then
    assert is_cimd_client_id(client_id) is False


def test_is_cimd_client_id__http_url__returns_false() -> None:
    from oauth2_metadata.cimd import is_cimd_client_id

    # Given
    client_id = "http://example.com/metadata"

    # When / Then
    assert is_cimd_client_id(client_id) is False


# ---------------------------------------------------------------------------
# cimd module: _is_public_hostname
# ---------------------------------------------------------------------------


def test_is_public_hostname__localhost__returns_false() -> None:
    from oauth2_metadata.cimd import _is_public_hostname

    # Given
    hostname = "localhost"

    # When / Then
    assert _is_public_hostname(hostname) is False


def test_is_public_hostname__nonexistent_host__returns_false() -> None:
    from oauth2_metadata.cimd import _is_public_hostname

    # Given
    hostname = "this-host-does-not-exist.invalid"

    # When / Then
    assert _is_public_hostname(hostname) is False


def test_is_public_hostname__private_ip__returns_false() -> None:
    from oauth2_metadata.cimd import _is_public_hostname

    # Given
    # Mock getaddrinfo to return a private IP.
    with patch("oauth2_metadata.cimd.socket.getaddrinfo") as mock_gai:
        mock_gai.return_value = [
            (2, 1, 6, "", ("192.168.1.1", 0)),
        ]

        # When / Then
        assert _is_public_hostname("internal.example.com") is False


def test_is_public_hostname__public_ip__returns_true() -> None:
    from oauth2_metadata.cimd import _is_public_hostname

    # Given
    with patch("oauth2_metadata.cimd.socket.getaddrinfo") as mock_gai:
        mock_gai.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 0)),
        ]

        # When / Then
        assert _is_public_hostname("example.com") is True


# ---------------------------------------------------------------------------
# cimd module: _validate_cimd_document
# ---------------------------------------------------------------------------

CLIENT_ID_URL = "https://example.com/oauth/metadata"


def test_validate_cimd_document__valid_document__returns_metadata() -> None:
    from oauth2_metadata.cimd import _validate_cimd_document

    # Given
    doc = {
        "client_id": CLIENT_ID_URL,
        "client_name": "Test App",
        "redirect_uris": ["https://example.com/callback"],
    }

    # When
    result = _validate_cimd_document(CLIENT_ID_URL, doc)

    # Then
    assert result["client_name"] == "Test App"
    assert result["redirect_uris"] == ["https://example.com/callback"]
    assert result["token_endpoint_auth_method"] == "none"


def test_validate_cimd_document__missing_token_endpoint_auth_method__defaults_to_none() -> (
    None
):
    from oauth2_metadata.cimd import _validate_cimd_document

    # Given
    doc = {
        "client_id": CLIENT_ID_URL,
        "redirect_uris": ["https://example.com/callback"],
    }

    # When
    result = _validate_cimd_document(CLIENT_ID_URL, doc)

    # Then
    assert result["token_endpoint_auth_method"] == "none"


def test_validate_cimd_document__client_id_mismatch__raises_value_error() -> None:
    from oauth2_metadata.cimd import _validate_cimd_document

    # Given
    doc = {
        "client_id": "https://other.com/metadata",
        "redirect_uris": ["https://example.com/callback"],
    }

    # When / Then
    with pytest.raises(ValueError, match="mismatch"):
        _validate_cimd_document(CLIENT_ID_URL, doc)


def test_validate_cimd_document__missing_redirect_uris__raises_value_error() -> None:
    from oauth2_metadata.cimd import _validate_cimd_document

    # Given
    doc = {"client_id": CLIENT_ID_URL}

    # When / Then
    with pytest.raises(ValueError, match="redirect_uris"):
        _validate_cimd_document(CLIENT_ID_URL, doc)


def test_validate_cimd_document__empty_redirect_uris__raises_value_error() -> None:
    from oauth2_metadata.cimd import _validate_cimd_document

    # Given
    doc = {"client_id": CLIENT_ID_URL, "redirect_uris": []}

    # When / Then
    with pytest.raises(ValueError, match="redirect_uris"):
        _validate_cimd_document(CLIENT_ID_URL, doc)


@pytest.mark.parametrize(
    "auth_method",
    ["client_secret_basic", "client_secret_post"],
    ids=["secret-basic", "secret-post"],
)
def test_validate_cimd_document__secret_based_auth_method__raises_value_error(
    auth_method: str,
) -> None:
    from oauth2_metadata.cimd import _validate_cimd_document

    # Given
    doc = {
        "client_id": CLIENT_ID_URL,
        "redirect_uris": ["https://example.com/callback"],
        "token_endpoint_auth_method": auth_method,
    }

    # When / Then
    with pytest.raises(ValueError, match="secret-based"):
        _validate_cimd_document(CLIENT_ID_URL, doc)


def test_validate_cimd_document__private_key_jwt__raises_value_error() -> None:
    from oauth2_metadata.cimd import _validate_cimd_document

    # Given
    doc = {
        "client_id": CLIENT_ID_URL,
        "redirect_uris": ["https://example.com/callback"],
        "token_endpoint_auth_method": "private_key_jwt",
    }

    # When / Then
    with pytest.raises(ValueError, match="not yet implemented"):
        _validate_cimd_document(CLIENT_ID_URL, doc)


def test_validate_cimd_document__no_client_name__falls_back_to_hostname() -> None:
    from oauth2_metadata.cimd import _validate_cimd_document

    # Given
    doc = {
        "client_id": CLIENT_ID_URL,
        "redirect_uris": ["https://example.com/callback"],
    }

    # When
    result = _validate_cimd_document(CLIENT_ID_URL, doc)

    # Then
    assert result["client_name"] == "example.com"


def test_validate_cimd_document__invalid_redirect_uri_in_doc__raises_value_error() -> (
    None
):
    from oauth2_metadata.cimd import _validate_cimd_document

    # Given
    doc = {
        "client_id": CLIENT_ID_URL,
        "redirect_uris": ["http://evil.example.com/callback"],
    }

    # When / Then
    with pytest.raises(ValueError, match="redirect_uri"):
        _validate_cimd_document(CLIENT_ID_URL, doc)


# ---------------------------------------------------------------------------
# cimd module: _fetch_cimd_document
# ---------------------------------------------------------------------------


def test_fetch_cimd_document__non_https__raises_value_error() -> None:
    from oauth2_metadata.cimd import _fetch_cimd_document

    # Given
    url = "http://example.com/metadata"

    # When / Then
    with pytest.raises(ValueError, match="HTTPS"):
        _fetch_cimd_document(url)


def test_fetch_cimd_document__url_too_long__raises_value_error() -> None:
    from oauth2_metadata.cimd import _fetch_cimd_document

    # Given
    long_url = "https://example.com/" + "a" * 200

    # When / Then
    with pytest.raises(ValueError, match="exceeds"):
        _fetch_cimd_document(long_url)


def test_fetch_cimd_document__no_hostname__raises_value_error() -> None:
    from oauth2_metadata.cimd import _fetch_cimd_document

    # Given
    url = "https:///path-only"

    # When / Then
    with pytest.raises(ValueError, match="hostname"):
        _fetch_cimd_document(url)


def test_fetch_cimd_document__private_hostname__raises_value_error() -> None:
    from oauth2_metadata.cimd import _fetch_cimd_document

    # Given
    with patch("oauth2_metadata.cimd._is_public_hostname", return_value=False):
        # When / Then
        with pytest.raises(ValueError, match="public address"):
            _fetch_cimd_document("https://internal.corp/metadata")


def test_fetch_cimd_document__http_error__raises_value_error() -> None:
    from oauth2_metadata.cimd import _fetch_cimd_document

    # Given
    with (
        patch("oauth2_metadata.cimd._is_public_hostname", return_value=True),
        patch("oauth2_metadata.cimd.requests.get") as mock_get,
    ):
        mock_get.side_effect = requests.ConnectionError("unreachable")

        # When / Then
        with pytest.raises(ValueError, match="Failed to fetch"):
            _fetch_cimd_document("https://example.com/metadata")


def test_fetch_cimd_document__non_json_response__raises_value_error() -> None:
    from oauth2_metadata.cimd import _fetch_cimd_document

    # Given
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("not JSON")

    with (
        patch("oauth2_metadata.cimd._is_public_hostname", return_value=True),
        patch("oauth2_metadata.cimd.requests.get", return_value=mock_response),
    ):
        # When / Then
        with pytest.raises(ValueError, match="not valid JSON"):
            _fetch_cimd_document("https://example.com/metadata")


def test_fetch_cimd_document__success__returns_dict() -> None:
    from oauth2_metadata.cimd import _fetch_cimd_document

    # Given
    expected = {"client_id": "https://example.com/metadata", "redirect_uris": []}
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = expected

    # When
    with (
        patch("oauth2_metadata.cimd._is_public_hostname", return_value=True),
        patch("oauth2_metadata.cimd.requests.get", return_value=mock_response),
    ):
        result = _fetch_cimd_document("https://example.com/metadata")

    # Then
    assert result == expected


# ---------------------------------------------------------------------------
# cimd module: resolve_cimd_client
# ---------------------------------------------------------------------------


def _mock_cimd_doc(
    client_id: str = "https://example.com/oauth/metadata",
    client_name: str = "Test CIMD App",
    redirect_uris: list[str] | None = None,
    **extra: object,
) -> dict:
    doc: dict = {
        "client_id": client_id,
        "client_name": client_name,
        "redirect_uris": redirect_uris or ["https://example.com/callback"],
    }
    doc.update(extra)
    return doc


@pytest.mark.django_db()
def test_resolve_cimd_client__valid_document__creates_application() -> None:
    from oauth2_metadata.cimd import resolve_cimd_client

    # Given
    doc = _mock_cimd_doc(client_id=CLIENT_ID_URL)

    # When
    with (
        patch("oauth2_metadata.cimd._fetch_cimd_document", return_value=doc),
        patch("oauth2_metadata.cimd.cache"),
    ):
        app = resolve_cimd_client(CLIENT_ID_URL)

    # Then
    assert app is not None
    assert app.client_id == CLIENT_ID_URL
    assert app.name == "Test CIMD App"
    assert app.client_type == Application.CLIENT_PUBLIC


@pytest.mark.django_db()
def test_resolve_cimd_client__valid_document__upserts_existing_application() -> None:
    from oauth2_metadata.cimd import resolve_cimd_client

    # Given
    doc = _mock_cimd_doc(client_id=CLIENT_ID_URL, client_name="V1")
    with (
        patch("oauth2_metadata.cimd._fetch_cimd_document", return_value=doc),
        patch("oauth2_metadata.cimd.cache"),
    ):
        app1 = resolve_cimd_client(CLIENT_ID_URL)

    doc2 = _mock_cimd_doc(client_id=CLIENT_ID_URL, client_name="V2")

    # When
    with (
        patch("oauth2_metadata.cimd._fetch_cimd_document", return_value=doc2),
        patch("oauth2_metadata.cimd.cache"),
    ):
        app2 = resolve_cimd_client(CLIENT_ID_URL)

    # Then
    assert app1 is not None
    assert app2 is not None
    assert app1.pk == app2.pk
    app2.refresh_from_db()
    assert app2.name == "V2"


@pytest.mark.django_db()
def test_resolve_cimd_client__fetch_failure__returns_none_and_logs(
    log: StructuredLogCapture,
) -> None:
    from oauth2_metadata.cimd import resolve_cimd_client

    # Given / When
    with (
        patch(
            "oauth2_metadata.cimd._fetch_cimd_document",
            side_effect=ValueError("unreachable"),
        ),
        patch("oauth2_metadata.cimd.cache"),
    ):
        app = resolve_cimd_client(CLIENT_ID_URL)

    # Then
    assert app is None
    assert any(e["event"] == "cimd.rejected" for e in log.events)


@pytest.mark.django_db()
def test_resolve_cimd_client__fetch_failure__increments_rejected_metric(
    assert_metric: AssertMetricFixture,
) -> None:
    from oauth2_metadata.cimd import resolve_cimd_client

    # Given / When
    with (
        patch(
            "oauth2_metadata.cimd._fetch_cimd_document",
            side_effect=ValueError("bad"),
        ),
        patch("oauth2_metadata.cimd.cache"),
    ):
        resolve_cimd_client(CLIENT_ID_URL)

    # Then
    assert_metric(
        name="flagsmith_oauth2_cimd_resolutions_total",
        labels={"outcome": "rejected"},
        value=1,
    )


@pytest.mark.django_db()
def test_resolve_cimd_client__valid_document__increments_resolved_metric(
    assert_metric: AssertMetricFixture,
) -> None:
    from oauth2_metadata.cimd import resolve_cimd_client

    # Given
    doc = _mock_cimd_doc(client_id=CLIENT_ID_URL)

    # When
    with (
        patch("oauth2_metadata.cimd._fetch_cimd_document", return_value=doc),
        patch("oauth2_metadata.cimd.cache"),
    ):
        resolve_cimd_client(CLIENT_ID_URL)

    # Then
    assert_metric(
        name="flagsmith_oauth2_cimd_resolutions_total",
        labels={"outcome": "resolved"},
        value=1,
    )


@pytest.mark.django_db()
def test_resolve_cimd_client__cached_app__skips_fetch() -> None:
    from oauth2_metadata.cimd import resolve_cimd_client

    # Given
    # Pre-create an Application.
    app = Application.objects.create(
        client_id=CLIENT_ID_URL,
        name="Cached App",
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris="https://example.com/callback",
    )

    # When
    with (
        patch("oauth2_metadata.cimd.cache") as mock_cache,
        patch("oauth2_metadata.cimd._fetch_cimd_document") as mock_fetch,
    ):
        mock_cache.get.return_value = app.pk
        result = resolve_cimd_client(CLIENT_ID_URL)

    # Then
    assert result is not None
    assert result.pk == app.pk
    mock_fetch.assert_not_called()


@pytest.mark.django_db()
def test_resolve_cimd_client__cached_app_deleted__falls_through_to_fetch() -> None:
    from oauth2_metadata.cimd import resolve_cimd_client

    # Given
    doc = _mock_cimd_doc(client_id=CLIENT_ID_URL)

    # When
    with (
        patch("oauth2_metadata.cimd.cache") as mock_cache,
        patch("oauth2_metadata.cimd._fetch_cimd_document", return_value=doc),
    ):
        # Cache returns a PK that no longer exists.
        mock_cache.get.return_value = 999999
        result = resolve_cimd_client(CLIENT_ID_URL)

    # Then
    assert result is not None
    assert result.client_id == CLIENT_ID_URL
    mock_cache.delete.assert_called_once()
