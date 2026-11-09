from django.conf import settings
from django.utils import timezone
from rest_framework.response import Response
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import SlidingToken

from custom_auth.jwt_cookie.constants import JWT_SLIDING_COOKIE_KEY
from users.models import FFAdminUser


def authorise_response(user: FFAdminUser, response: Response) -> Response:
    sliding_token = SlidingToken.for_user(user)
    response.set_cookie(
        JWT_SLIDING_COOKIE_KEY,
        str(sliding_token),
        httponly=True,
        secure=settings.USE_SECURE_COOKIES,
        samesite=settings.COOKIE_SAME_SITE,  # type: ignore[arg-type]
    )
    return response


def blacklist_user_tokens(user: FFAdminUser) -> None:
    outstanding_tokens = OutstandingToken.objects.filter(
        user=user,
        expires_at__gt=timezone.now(),
        blacklistedtoken__isnull=True,
    )
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=token) for token in outstanding_tokens],
        ignore_conflicts=True,
    )
