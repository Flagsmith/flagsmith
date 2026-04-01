from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from oauth2_provider.models import Application


def validate_redirect_uri(uri: str) -> str:
    """Validate a single redirect URI per DCR policy.

    Rules:
    - HTTPS required for all redirect URIs
    - No wildcards, exact match only
    - No fragment components
    - localhost exception: http://localhost:* and http://127.0.0.1:* permitted
    """
    parsed = urlparse(uri)

    if not parsed.scheme or not parsed.netloc:
        raise ValidationError(f"Invalid URI: {uri}")

    if "*" in uri:
        raise ValidationError(f"Wildcards are not permitted in redirect URIs: {uri}")

    if parsed.fragment:
        raise ValidationError(f"Fragment components are not permitted: {uri}")

    is_localhost = parsed.hostname in ("localhost", "127.0.0.1")

    if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
        raise ValidationError(
            f"HTTPS is required for redirect URIs (localhost excepted): {uri}"
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
        redirect_uris=" ".join(redirect_uris),
        skip_authorization=False,
    )
    return application
