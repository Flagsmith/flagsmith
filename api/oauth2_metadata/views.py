from typing import Any

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from rest_framework import status as drf_status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from oauth2_metadata.serializers import DCRRequestSerializer
from oauth2_metadata.services import create_oauth2_application


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


class DynamicClientRegistrationView(APIView):
    """RFC 7591 Dynamic Client Registration endpoint."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "dcr_register"

    # Map DRF serializer field names to RFC 7591 error codes.
    _rfc7591_error_codes: dict[str, str] = {
        "redirect_uris": "invalid_redirect_uri",
        "client_name": "invalid_client_metadata",
        "grant_types": "invalid_client_metadata",
        "response_types": "invalid_client_metadata",
        "token_endpoint_auth_method": "invalid_client_metadata",
    }

    def post(self, request: Request) -> Response:
        serializer = DCRRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return self._rfc7591_error_response(serializer.errors)

        data = serializer.validated_data

        application = create_oauth2_application(
            client_name=data["client_name"],
            redirect_uris=data["redirect_uris"],
        )

        return Response(
            {
                "client_id": application.client_id,
                "client_name": application.name,
                "redirect_uris": data["redirect_uris"],
                "grant_types": data["grant_types"],
                "response_types": data["response_types"],
                "token_endpoint_auth_method": data["token_endpoint_auth_method"],
                "client_id_issued_at": int(application.created.timestamp()),
            },
            status=drf_status.HTTP_201_CREATED,
        )

    def _rfc7591_error_response(self, errors: dict[str, list[str]]) -> Response:
        """Format validation errors per RFC 7591 section 3.2.2."""
        first_field = next(iter(errors))
        error_code = self._rfc7591_error_codes.get(
            first_field, "invalid_client_metadata"
        )
        messages = errors[first_field]
        description = messages[0] if isinstance(messages[0], str) else str(messages[0])

        return Response(
            {
                "error": error_code,
                "error_description": description,
            },
            status=drf_status.HTTP_400_BAD_REQUEST,
        )
