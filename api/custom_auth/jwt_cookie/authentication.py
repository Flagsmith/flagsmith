from rest_framework.request import Request
from rest_framework_simplejwt.authentication import AuthUser, JWTAuthentication
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.tokens import Token

from custom_auth.jwt_cookie.constants import (
    ACCESS_TOKEN_COOKIE_KEY,
    REFRESH_TOKEN_COOKIE_KEY,
)


class JWTCookieAuthentication(JWTAuthentication):
    def authenticate_header(self, request: Request) -> str:
        return f'Cookie realm="{self.www_authenticate_realm}"'

    def authenticate(self, request: Request) -> tuple[AuthUser, Token] | None:

        if raw_access_token := request.COOKIES.get(ACCESS_TOKEN_COOKIE_KEY):
            try:
                # TODO https://github.com/jazzband/djangorestframework-simplejwt/pull/889
                validated_access_token = self.get_validated_token(raw_access_token)  # type: ignore[arg-type]
                # TODO https://github.com/jazzband/djangorestframework-simplejwt/pull/890
                return self.get_user(validated_access_token), validated_access_token  # type: ignore[return-value]
            except (InvalidToken, TokenError, AuthenticationFailed):
                pass

        if raw_refresh_token := request.COOKIES.get(REFRESH_TOKEN_COOKIE_KEY):
            try:
                validated_refresh_token = self.get_validated_token(raw_refresh_token)  # type: ignore[arg-type]
                return self.get_user(validated_refresh_token), validated_refresh_token  # type: ignore[return-value]
            except (InvalidToken, TokenError, AuthenticationFailed):
                pass

        return None
