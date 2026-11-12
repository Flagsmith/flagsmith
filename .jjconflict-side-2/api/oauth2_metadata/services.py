import logging
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from oauth2_provider.generators import generate_client_secret
from oauth2_provider.models import Application

from oauth2_metadata.dataclasses import RegisteredClient

logger = logging.getLogger(__name__)


# Schemes a browser may execute or read local content through; never
# acceptable as redirect targets.
FORBIDDEN_REDIRECT_URI_SCHEMES = frozenset(
    {"javascript", "data", "vbscript", "file", "about", "blob"}
)


def validate_redirect_uri(uri: str) -> str:
    """Validate a single redirect URI per DCR policy.

    Rules:
    - No wildcards, exact match only
    - No fragment components
    - https:// permitted for any host
    - http:// permitted for loopback addresses only (RFC 8252 §7.3)
    - Private-use schemes (e.g. claude://, com.example.app:/) permitted
      for native app clients (RFC 8252 §7.1), excluding schemes a browser
      treats as executable
    """
    try:
        parsed = urlparse(uri)
        _ = parsed.port  # Raises on malformed or out-of-range ports.
    except ValueError as e:
        # e.g. malformed IPv6 authority such as https://[::1
        raise ValidationError(f"Invalid URI: {uri}") from e

    if not parsed.scheme or not (parsed.netloc or parsed.path):
        raise ValidationError(f"Invalid URI: {uri}")

    if "*" in uri:
        raise ValidationError(f"Wildcards are not permitted in redirect URIs: {uri}")

    if parsed.fragment:
        raise ValidationError(f"Fragment components are not permitted: {uri}")

    scheme = parsed.scheme.lower()

    if scheme in FORBIDDEN_REDIRECT_URI_SCHEMES:
        raise ValidationError(f"Scheme is not permitted in redirect URIs: {uri}")

    if scheme in ("http", "https") and not parsed.hostname:
        raise ValidationError(f"Invalid URI: {uri}")

    is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")

    if scheme == "http" and not is_localhost:
        raise ValidationError(
            f"HTTPS is required for http(s) redirect URIs (localhost excepted): {uri}"
        )

    return uri


def create_oauth2_application(
    *,
    client_name: str,
    redirect_uris: list[str],
    token_endpoint_auth_method: str = "none",
) -> RegisteredClient:
    """Create an OAuth2 application for dynamic client registration."""
    client_secret = ""
    client_type = Application.CLIENT_PUBLIC
    if token_endpoint_auth_method != "none":
        client_secret = generate_client_secret()
        client_type = Application.CLIENT_CONFIDENTIAL

    application: Application = Application.objects.create(
        name=client_name,
        client_type=client_type,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        client_secret=client_secret,
        redirect_uris=" ".join(redirect_uris),
        skip_authorization=False,
    )
    logger.info(
        "OAuth2 DCR: registered application %s (client_id=%s, client_type=%s).",
        client_name,
        application.client_id,
        client_type,
    )
    return RegisteredClient(application=application, client_secret=client_secret)
