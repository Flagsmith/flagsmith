from typing import Any
from urllib.parse import urlencode, urlparse, urlunparse

import structlog
from django.http import HttpRequest, HttpResponse, JsonResponse, QueryDict
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from oauth2_provider.exceptions import OAuthToolkitError
from oauth2_provider.models import get_application_model
from oauth2_provider.scopes import get_scopes_backend
from oauth2_provider.views import TokenView
from oauth2_provider.views.mixins import OAuthLibMixin
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from oauth2_metadata.cimd import is_cimd_client_id, resolve_cimd_client
from oauth2_metadata.dataclasses import OAuthConfig
from oauth2_metadata.mappers import map_drf_error_to_rfc7591_error_body
from oauth2_metadata.metrics import flagsmith_oauth2_dcr_registrations_total
from oauth2_metadata.serializers import (
    TOKEN_ENDPOINT_AUTH_METHODS,
    DCRRequestSerializer,
    OAuthConsentSerializer,
)
from oauth2_metadata.services import create_oauth2_application

logger = structlog.get_logger("oauth2_metadata")


@csrf_exempt
@require_GET
def authorization_server_metadata(request: HttpRequest) -> JsonResponse:
    """RFC 8414 OAuth 2.0 Authorization Server Metadata."""
    oauth = OAuthConfig.from_settings()

    metadata = {
        "issuer": oauth.api_url,
        "authorization_endpoint": f"{oauth.frontend_url}/oauth/authorize/",
        "token_endpoint": f"{oauth.api_url}/o/token/",
        "registration_endpoint": f"{oauth.api_url}/o/register/",
        "revocation_endpoint": f"{oauth.api_url}/o/revoke_token/",
        "introspection_endpoint": f"{oauth.api_url}/o/introspect/",
        "scopes_supported": list(oauth.scopes.keys()),
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
            "none",
        ],
        "introspection_endpoint_auth_methods_supported": ["none"],
        "client_id_metadata_document_supported": True,
    }

    return JsonResponse(metadata)


class OAuthAuthorizeView(OAuthLibMixin, APIView):  # type: ignore[misc]
    """Validate an OAuth authorisation request and process consent decisions."""

    permission_classes = [IsAuthenticated]

    def _ensure_cimd_client(self, request: HttpRequest) -> str | None:
        """If client_id is a CIMD URL, resolve it and return the client_id.

        Returns None if resolution fails, so the caller can return an error.
        The client_id in the request is NOT mutated — DOT will look it up
        by the URL value which is now stored as Application.client_id.
        """
        client_id = request.GET.get("client_id", "")
        if not is_cimd_client_id(client_id):
            return client_id  # Not a CIMD client_id, let DOT handle it.
        app = resolve_cimd_client(client_id)
        if app is None:
            return None
        return client_id

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Validate an authorisation request and return application info."""
        # Bridge DRF auth to Django request so DOT sees the authenticated user.
        request._request.user = request.user

        resolved = self._ensure_cimd_client(request._request)
        if resolved is None:
            return Response(
                {
                    "error": "invalid_client",
                    "error_description": "Could not resolve CIMD client metadata.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            scopes, credentials = self.validate_authorization_request(request._request)
        except OAuthToolkitError as e:
            oauthlib_error = e.oauthlib_error
            return Response(
                {
                    "error": getattr(oauthlib_error, "error", "invalid_request"),
                    "error_description": getattr(oauthlib_error, "description", str(e)),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        Application = get_application_model()
        application = Application.objects.get(
            client_id=credentials["client_id"],
        )
        all_scopes = get_scopes_backend().get_all_scopes()
        scopes_dict: dict[str, str] = {s: all_scopes.get(s, s) for s in scopes}
        return Response(
            {
                "application": {
                    "name": application.name,
                    "client_id": application.client_id,
                },
                "scopes": scopes_dict,
                "redirect_uri": credentials.get("redirect_uri", ""),
                # skip_authorization is safe to reuse here: this custom view
                # always shows the consent screen regardless of this flag.
                # We only use it as a trust signal for the frontend UI.
                "is_verified": bool(application.skip_authorization),
            }
        )

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Process a consent decision and return the redirect URI."""
        serializer = OAuthConsentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data
        allow: bool = data.pop("allow")

        # Bridge DRF auth to Django request so DOT sees the authenticated user.
        request._request.user = request.user

        # DOT's validate_authorization_request reads OAuth params from GET
        # and also from request.get_full_path() which uses META['QUERY_STRING'].
        # This is necessary because DOT's OAuthLibMixin is designed for
        # form-based flows where params arrive via GET. If a DOT upgrade
        # changes how it reads params, this will need updating.
        query = QueryDict(mutable=True)
        for key, value in data.items():
            query[key] = str(value)
        request._request.GET = query  # type: ignore[assignment]
        request._request.META["QUERY_STRING"] = query.urlencode()

        resolved = self._ensure_cimd_client(request._request)
        if resolved is None:
            return Response(
                {
                    "error": "invalid_client",
                    "error_description": "Could not resolve CIMD client metadata.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            scopes, credentials = self.validate_authorization_request(request._request)
        except OAuthToolkitError as e:
            oauthlib_error = e.oauthlib_error
            return Response(
                {
                    "error": getattr(oauthlib_error, "error", "invalid_request"),
                    "error_description": getattr(oauthlib_error, "description", str(e)),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            scopes_str = " ".join(scopes) if isinstance(scopes, list) else scopes
            uri, _headers, _body, _status = self.create_authorization_response(
                request._request, scopes_str, credentials, allow
            )
        except OAuthToolkitError:
            # User denied access -- build the error redirect manually.
            redirect_uri = credentials.get("redirect_uri", data.get("redirect_uri", ""))
            state = credentials.get("state", data.get("state", ""))
            error_params: dict[str, str] = {"error": "access_denied"}
            if state:
                error_params["state"] = state
            parsed = urlparse(str(redirect_uri))
            uri = urlunparse(parsed._replace(query=urlencode(error_params)))

        return Response({"redirect_uri": uri})


class DynamicClientRegistrationView(APIView):
    """RFC 7591 Dynamic Client Registration endpoint."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "dcr_register"

    def post(self, request: Request) -> Response:
        serializer = DCRRequestSerializer(data=request.data)
        if not serializer.is_valid():
            error_body = map_drf_error_to_rfc7591_error_body(serializer.errors)
            payload = request.data if isinstance(request.data, dict) else {}
            self._count_registration(
                payload.get("token_endpoint_auth_method"), outcome="rejected"
            )
            logger.error(
                "registration.rejected",
                error=error_body["error"],
                error_description=error_body["error_description"],
                client__name=payload.get("client_name"),
                redirect_uris=payload.get("redirect_uris"),
                user_agent=request.headers.get("User-Agent", ""),
            )
            return Response(
                error_body,
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        registered = create_oauth2_application(
            client_name=data["client_name"],
            redirect_uris=data["redirect_uris"],
            token_endpoint_auth_method=data["token_endpoint_auth_method"],
        )
        self._count_registration(
            data["token_endpoint_auth_method"], outcome="registered"
        )

        application = registered.application
        response_body: dict[str, Any] = {
            "client_id": application.client_id,
            "client_name": application.name,
            "redirect_uris": data["redirect_uris"],
            "grant_types": data["grant_types"],
            "response_types": data["response_types"],
            "token_endpoint_auth_method": data["token_endpoint_auth_method"],
            "client_id_issued_at": int(application.created.timestamp()),
        }
        if registered.client_secret:
            response_body["client_secret"] = registered.client_secret
            # 0 means the secret never expires, per RFC 7591 §3.2.1.
            response_body["client_secret_expires_at"] = 0

        return Response(response_body, status=status.HTTP_201_CREATED)

    def _count_registration(self, auth_method: Any, outcome: str) -> None:
        # Requested method is client input; collapse unknown values to keep
        # metric cardinality bounded.
        if auth_method is None:
            auth_method = "none"
        if auth_method not in TOKEN_ENDPOINT_AUTH_METHODS:
            auth_method = "other"
        flagsmith_oauth2_dcr_registrations_total.labels(
            token_endpoint_auth_method=auth_method, outcome=outcome
        ).inc()


class CIMDTokenView(TokenView):
    """Token endpoint that resolves CIMD client_ids before DOT processing.

    Wraps DOT's TokenView so that when a client_id in the POST body is
    an HTTPS URL, we ensure the corresponding Application row exists
    before DOT attempts to look it up.
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        client_id = request.POST.get("client_id", "")
        if is_cimd_client_id(client_id):
            app = resolve_cimd_client(client_id)
            if app is None:
                return JsonResponse(
                    {"error": "invalid_client"},
                    status=400,
                )
        return super().post(request, *args, **kwargs)
