from typing import Any

from django.conf import settings
from djoser.views import TokenDestroyView  # type: ignore[import-untyped]
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from custom_auth.jwt_cookie.constants import (
    ACCESS_TOKEN_COOKIE_KEY,
    REFRESH_TOKEN_COOKIE_KEY,
)


class JWTTokenLogoutView(TokenDestroyView):  # type: ignore[misc]
    def post(self, request: Request) -> Response:
        response: Response = super().post(request)

        raw_refresh_token = request.COOKIES.get(REFRESH_TOKEN_COOKIE_KEY)
        if raw_refresh_token:
            refresh_token = RefreshToken(raw_refresh_token)  # type: ignore[arg-type]
            refresh_token.blacklist()

        response.delete_cookie(ACCESS_TOKEN_COOKIE_KEY)
        response.delete_cookie(REFRESH_TOKEN_COOKIE_KEY)
        return response


class JWTCookieTokenRefreshView(TokenRefreshView):
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if not (raw_refresh_token := request.COOKIES.get(REFRESH_TOKEN_COOKIE_KEY)):
            raise InvalidToken("No valid refresh token found in cookie")

        serializer = self.get_serializer(data={"refresh": raw_refresh_token})
        serializer.is_valid(raise_exception=True)

        response = Response(serializer.validated_data)

        response.set_cookie(
            ACCESS_TOKEN_COOKIE_KEY,
            str(serializer.validated_data["access"]),
            httponly=True,
            secure=settings.USE_SECURE_COOKIES,
            samesite=settings.COOKIE_SAME_SITE,  # type: ignore[arg-type]
            max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        )

        response.set_cookie(
            REFRESH_TOKEN_COOKIE_KEY,
            str(serializer.validated_data["refresh"]),
            httponly=True,
            secure=settings.USE_SECURE_COOKIES,
            samesite=settings.COOKIE_SAME_SITE,  # type: ignore[arg-type]
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        )

        return response
