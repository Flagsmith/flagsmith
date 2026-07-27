import logging
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from oauth2_provider.models import Application

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
    parsed = urlparse(uri)

    if not parsed.scheme or not (parsed.netloc or parsed.path):
        raise ValidationError(f"Invalid URI: {uri}")

    if "*" in uri:
        raise ValidationError(f"Wildcards are not permitted in redirect URIs: {uri}")

    if parsed.fragment:
        raise ValidationError(f"Fragment components are not permitted: {uri}")

    scheme = parsed.scheme.lower()

    if scheme in FORBIDDEN_REDIRECT_URI_SCHEMES:
        raise ValidationError(f"Scheme is not permitted in redirect URIs: {uri}")

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
) -> Application:
    """Create a public OAuth2 application for dynamic client registration."""
    application: Application = Application.objects.create(
        name=client_name,
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        client_secret="",
        redirect_uris=" ".join(redirect_uris),
        skip_authorization=False,
    )
    logger.info(
        "OAuth2 DCR: registered application %s (client_id=%s).",
        client_name,
        application.client_id,
    )
    return application
