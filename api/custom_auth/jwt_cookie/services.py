from django.conf import settings
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from custom_auth.jwt_cookie.constants import (
    ACCESS_TOKEN_COOKIE_KEY,
    REFRESH_TOKEN_COOKIE_KEY,
)
from users.models import FFAdminUser


def authorise_response(user: FFAdminUser, response: Response) -> Response:
    access_token = AccessToken.for_user(user)
    refresh_token = RefreshToken.for_user(user)
    response.set_cookie(
        ACCESS_TOKEN_COOKIE_KEY,
        str(access_token),
        httponly=True,
        secure=settings.USE_SECURE_COOKIES,
        samesite=settings.COOKIE_SAME_SITE, # type: ignore[arg-type]
        max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
    )
    response.set_cookie(
        REFRESH_TOKEN_COOKIE_KEY,
        str(refresh_token),
        httponly=True,
        secure=settings.USE_SECURE_COOKIES,
        samesite=settings.COOKIE_SAME_SITE,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
    )
    return response
