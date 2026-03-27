from typing import Any

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET


@csrf_exempt
@require_GET
def authorization_server_metadata(request: HttpRequest) -> JsonResponse:
    """RFC 8414 OAuth 2.0 Authorization Server Metadata."""
    api_url: str = settings.FLAGSMITH_API_URL.rstrip("/")
    frontend_url: str = settings.FLAGSMITH_FRONTEND_URL.rstrip("/")
    oauth2_settings: dict[str, Any] = settings.OAUTH2_PROVIDER
    scopes: dict[str, str] = oauth2_settings.get("SCOPES", {})

    metadata = {
        "issuer": api_url,
        "authorization_endpoint": f"{frontend_url}/oauth/authorize/",
        "token_endpoint": f"{api_url}/o/token/",
        "registration_endpoint": f"{api_url}/o/register/",
        "revocation_endpoint": f"{api_url}/o/revoke_token/",
        "introspection_endpoint": f"{api_url}/o/introspect/",
        "scopes_supported": list(scopes.keys()),
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
            "none",
        ],
        "introspection_endpoint_auth_methods_supported": ["none"],
    }

    return JsonResponse(metadata)
