"""Client ID Metadata Document (CIMD) resolution.

When a client_id is an HTTPS URL, the authorisation server fetches the
client metadata document from that URL instead of requiring DCR.
"""

import ipaddress
import socket
from urllib.parse import urlparse

import requests
import structlog
from django.core.cache import cache
from django.core.exceptions import ValidationError
from oauth2_provider.models import Application

from oauth2_metadata.metrics import flagsmith_oauth2_cimd_resolutions_total
from oauth2_metadata.services import validate_redirect_uri

logger = structlog.get_logger("oauth2_metadata")

# Cache resolved CIMD applications for 10 minutes to avoid hammering the
# client's metadata endpoint on every authorize/token call.
CIMD_CACHE_TTL_SECONDS = 60 * 10
CIMD_FETCH_TIMEOUT_SECONDS = 5

# Auth methods that require a shared secret — impossible without a
# registration step, so we reject these.
_SECRET_BASED_AUTH_METHODS = frozenset({"client_secret_basic", "client_secret_post"})
# Auth methods not yet implemented.
_UNSUPPORTED_AUTH_METHODS = frozenset({"private_key_jwt"})


# DOT's Application.client_id field has max_length=100.
# TODO: real-world CIMD URLs (e.g. Claude Code) can be long; consider a
# migration to increase Application.client_id max_length if this proves
# too restrictive.
_CLIENT_ID_MAX_LENGTH = 100


def is_cimd_client_id(client_id: str) -> bool:
    """Return True if client_id looks like an HTTPS URL."""
    return client_id.startswith("https://")


def _is_public_hostname(hostname: str) -> bool:
    """Return True if hostname resolves to at least one public IP address."""
    try:
        addrinfo = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False

    for family, _type, _proto, _canonname, sockaddr in addrinfo:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            return False
    return bool(addrinfo)


def _fetch_cimd_document(client_id_url: str) -> dict:
    """Fetch and return the JSON metadata document at client_id_url.

    Raises ValueError on any fetch/parse failure.
    """
    parsed = urlparse(client_id_url)
    if parsed.scheme != "https":
        raise ValueError(f"client_id must be an HTTPS URL: {client_id_url}")

    if len(client_id_url) > _CLIENT_ID_MAX_LENGTH:
        raise ValueError(
            f"client_id URL exceeds {_CLIENT_ID_MAX_LENGTH} characters: {client_id_url}"
        )

    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"client_id URL has no hostname: {client_id_url}")

    if not _is_public_hostname(hostname):
        raise ValueError(
            f"client_id hostname does not resolve to a public address: {hostname}"
        )

    # TODO: _is_public_hostname resolves DNS independently from requests.get,
    # leaving a small TOCTOU window for DNS rebinding attacks. A robust fix
    # would pin the resolved IP and connect to it directly.
    try:
        response = requests.get(
            client_id_url,
            timeout=CIMD_FETCH_TIMEOUT_SECONDS,
            allow_redirects=False,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ValueError(f"Failed to fetch CIMD document: {exc}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise ValueError(f"CIMD document is not valid JSON: {exc}") from exc


def _validate_cimd_document(client_id_url: str, doc: dict) -> dict:
    """Validate a CIMD document and return normalised metadata.

    Raises ValueError on validation failure.
    """
    # The document's client_id MUST match the URL it was fetched from.
    doc_client_id = doc.get("client_id")
    if doc_client_id != client_id_url:
        raise ValueError(
            f"CIMD client_id mismatch: document says {doc_client_id!r}, "
            f"expected {client_id_url!r}"
        )

    # redirect_uris is required.
    redirect_uris = doc.get("redirect_uris")
    if not redirect_uris or not isinstance(redirect_uris, list):
        raise ValueError("CIMD document must contain a non-empty redirect_uris array")

    # Validate each redirect URI against the same policy as DCR.
    for uri in redirect_uris:
        try:
            validate_redirect_uri(uri)
        except ValidationError as exc:
            raise ValueError(
                f"Invalid redirect_uri in CIMD document: {exc.message}"
            ) from exc

    # token_endpoint_auth_method: default to "none" if absent.
    auth_method = doc.get("token_endpoint_auth_method", "none")

    if auth_method in _SECRET_BASED_AUTH_METHODS:
        raise ValueError(
            f"CIMD clients cannot use secret-based auth method: {auth_method}. "
            f"No registration step exists to distribute a secret."
        )

    if auth_method in _UNSUPPORTED_AUTH_METHODS:
        raise ValueError(
            f"Auth method {auth_method} is not yet implemented for CIMD clients."
        )

    # client_name falls back to the hostname.
    parsed = urlparse(client_id_url)
    client_name = doc.get("client_name") or parsed.hostname or "CIMD client"

    return {
        "client_name": client_name,
        "redirect_uris": redirect_uris,
        "token_endpoint_auth_method": auth_method,
    }


def resolve_cimd_client(client_id_url: str) -> Application | None:
    """Resolve a CIMD client_id URL to a DOT Application.

    Returns the Application on success, None on failure (all failures
    are logged and counted).
    """
    cache_key = f"cimd:{client_id_url}"
    cached_app_pk = cache.get(cache_key)
    if cached_app_pk is not None:
        try:
            return Application.objects.get(pk=cached_app_pk)
        except Application.DoesNotExist:
            cache.delete(cache_key)

    try:
        doc = _fetch_cimd_document(client_id_url)
        metadata = _validate_cimd_document(client_id_url, doc)
    except ValueError as exc:
        logger.error(
            "cimd.rejected",
            client_id=client_id_url,
            reason=str(exc),
        )
        flagsmith_oauth2_cimd_resolutions_total.labels(outcome="rejected").inc()
        return None

    # Upsert: reuse an existing Application row keyed by the URL client_id,
    # or create one. This avoids littering Application rows.
    application, created = Application.objects.update_or_create(
        client_id=client_id_url,
        defaults={
            "name": metadata["client_name"],
            "client_type": Application.CLIENT_PUBLIC,
            "authorization_grant_type": Application.GRANT_AUTHORIZATION_CODE,
            "client_secret": "",
            "redirect_uris": " ".join(metadata["redirect_uris"]),
            "skip_authorization": False,
        },
    )

    action = "created" if created else "refreshed"
    logger.info(
        f"cimd.{action}",
        client_id=client_id_url,
        client_name=metadata["client_name"],
    )
    flagsmith_oauth2_cimd_resolutions_total.labels(outcome="resolved").inc()

    cache.set(cache_key, application.pk, CIMD_CACHE_TTL_SECONDS)
    return application
