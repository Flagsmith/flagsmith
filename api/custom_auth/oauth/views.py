import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.shortcuts import redirect
from drf_yasg.utils import swagger_auto_schema  # type: ignore[import-untyped]
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from api.serializers import ErrorSerializer
from custom_auth.jwt_cookie.services import authorise_response
from custom_auth.models import OIDCConfiguration
from custom_auth.oauth.exceptions import GithubError, GoogleError, OIDCError
from custom_auth.oauth.oidc import OIDCProvider
from custom_auth.oauth.serializers import (
    GithubLoginSerializer,
    GoogleLoginSerializer,
    OIDCConfigurationSerializer,
)
from custom_auth.serializers import CustomTokenSerializer

UserModel = get_user_model()

logger = logging.getLogger(__name__)

AUTH_ERROR_MESSAGE = "An error occurred authenticating with {}"
GITHUB_AUTH_ERROR_MESSAGE = AUTH_ERROR_MESSAGE.format("GITHUB")
GOOGLE_AUTH_ERROR_MESSAGE = AUTH_ERROR_MESSAGE.format("GOOGLE")
OIDC_AUTH_ERROR_MESSAGE = AUTH_ERROR_MESSAGE.format("OIDC")


@swagger_auto_schema(
    method="post",
    request_body=GoogleLoginSerializer,
    responses={200: CustomTokenSerializer, 502: ErrorSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_with_google(request):  # type: ignore[no-untyped-def]
    try:
        serializer = GoogleLoginSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        token = serializer.save()
        if settings.COOKIE_AUTH_ENABLED:
            return authorise_response(token.user, Response(status=HTTP_204_NO_CONTENT))
        return Response(data=CustomTokenSerializer(instance=token).data)
    except GoogleError as e:
        logger.warning("%s: %s" % (GOOGLE_AUTH_ERROR_MESSAGE, str(e)))
        return Response(
            data={"message": GOOGLE_AUTH_ERROR_MESSAGE},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@swagger_auto_schema(
    method="post",
    request_body=GithubLoginSerializer,
    responses={200: CustomTokenSerializer, 502: ErrorSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_with_github(request):  # type: ignore[no-untyped-def]
    try:
        serializer = GithubLoginSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        token = serializer.save()
        if settings.COOKIE_AUTH_ENABLED:
            return authorise_response(token.user, Response(status=HTTP_204_NO_CONTENT))
        return Response(data=CustomTokenSerializer(instance=token).data)
    except GithubError as e:
        logger.warning("%s: %s" % (GITHUB_AUTH_ERROR_MESSAGE, str(e)))
        return Response(
            data={"message": GITHUB_AUTH_ERROR_MESSAGE},
            status=status.HTTP_502_BAD_GATEWAY,
        )


class OIDCConfigurationViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet for managing OIDC configurations. Filtered by ?organisation=<id>."""

    serializer_class = OIDCConfigurationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "name"

    def get_queryset(self):  # type: ignore[no-untyped-def]
        organisation_id = self.request.query_params.get("organisation")
        if organisation_id:
            return OIDCConfiguration.objects.filter(organisation_id=organisation_id)
        return OIDCConfiguration.objects.none()


@api_view(["GET"])
@permission_classes([AllowAny])
def oidc_authorize(request: Request, name: str) -> Response:
    """Initiate the OIDC Authorization Code flow by redirecting to the provider."""
    try:
        oidc_config = OIDCConfiguration.objects.get(name=name)
    except OIDCConfiguration.DoesNotExist:
        return Response(
            {"detail": "OIDC configuration not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    provider = OIDCProvider(
        provider_url=oidc_config.provider_url,
        client_id=oidc_config.client_id,
        client_secret=oidc_config.client_secret,
    )
    callback_url = request.build_absolute_uri(f"/api/v1/auth/oauth/oidc/{name}/callback/")
    try:
        authorization_url = provider.get_authorization_url(redirect_uri=callback_url)
    except OIDCError as e:
        logger.warning("%s: %s" % (OIDC_AUTH_ERROR_MESSAGE, str(e)))
        return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    return redirect(authorization_url)


@api_view(["GET"])
@permission_classes([AllowAny])
def oidc_callback(request: Request, name: str) -> Response:
    """Handle the OIDC callback, exchange code for tokens, and log the user in."""
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        logger.warning("OIDC callback error for '%s': %s", name, error)
        return Response(
            {"detail": f"OIDC provider error: {error}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not code or not state:
        return Response(
            {"detail": "Missing 'code' or 'state' in OIDC callback."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        oidc_config = OIDCConfiguration.objects.get(name=name)
    except OIDCConfiguration.DoesNotExist:
        return Response(
            {"detail": "OIDC configuration not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    provider = OIDCProvider(
        provider_url=oidc_config.provider_url,
        client_id=oidc_config.client_id,
        client_secret=oidc_config.client_secret,
    )
    callback_url = request.build_absolute_uri(f"/api/v1/auth/oauth/oidc/{name}/callback/")

    try:
        user_info = provider.exchange_code_for_user_info(
            code=code, state=state, redirect_uri=callback_url
        )
    except OIDCError as e:
        logger.warning("%s: %s" % (OIDC_AUTH_ERROR_MESSAGE, str(e)))
        return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    email: str = user_info["email"]
    existing_user = UserModel.objects.filter(email__iexact=email).first()

    if existing_user:
        user = existing_user
    else:
        user = UserModel.objects.create(
            email=email.lower(),
            first_name=user_info.get("first_name", ""),
            last_name=user_info.get("last_name", ""),
        )

    user_logged_in.send(sender=UserModel, request=request, user=user)
    token, _ = Token.objects.get_or_create(user=user)

    frontend_url = oidc_config.frontend_url or getattr(settings, "FRONTEND_URL", "/")

    if settings.COOKIE_AUTH_ENABLED:
        response = redirect(frontend_url)
        return authorise_response(user, response)

    return redirect(f"{frontend_url}?oidc_token={token.key}")
