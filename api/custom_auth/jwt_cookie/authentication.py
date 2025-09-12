from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.tokens import Token

from custom_auth.jwt_cookie.constants import JWT_SLIDING_COOKIE_KEY
from users.models import FFAdminUser


class JWTCookieAuthentication(JWTAuthentication):
    def authenticate_header(self, request: Request) -> str:
        return f'Cookie realm="{self.www_authenticate_realm}"'

    def authenticate(self, request: Request) -> tuple[FFAdminUser, Token] | None:
        if raw_token := request.COOKIES.get(JWT_SLIDING_COOKIE_KEY):
            try:
                validated_token = self.get_validated_token(raw_token)  # type: ignore[arg-type]
                return self.get_user(validated_token), validated_token  # type: ignore[return-value]
            except (InvalidToken, TokenError, AuthenticationFailed):
                return None
        return None
