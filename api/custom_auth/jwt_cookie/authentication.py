from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.tokens import Token

from custom_auth.jwt_cookie.constants import ACCESS_TOKEN_COOKIE_KEY, REFRESH_TOKEN_COOKIE_KEY
from users.models import FFAdminUser


class JWTCookieAuthentication(JWTAuthentication):
    def authenticate_header(self, request: Request) -> str:
        return f'Cookie realm="{self.www_authenticate_realm}"'

    def authenticate(self, request: Request) -> tuple[FFAdminUser, Token] | None:
        raw_access_token = request.COOKIES.get(ACCESS_TOKEN_COOKIE_KEY)
        raw_refresh_token = request.COOKIES.get(REFRESH_TOKEN_COOKIE_KEY)

        if raw_access_token:
            try:
                validated_access_token = self.get_validated_token(raw_access_token)  # type: ignore[arg-type]
                return self.get_user(validated_access_token), validated_access_token  # type: ignore[return-value]
            except (InvalidToken, TokenError, AuthenticationFailed):
                pass

        if raw_refresh_token:
            try:
                validated_refresh_token = self.get_validated_token(raw_refresh_token)  # type: ignore[arg-type]
                return self.get_user(validated_refresh_token), validated_refresh_token  # type: ignore[return-value]
            except (InvalidToken, TokenError, AuthenticationFailed):
                pass

        return None
