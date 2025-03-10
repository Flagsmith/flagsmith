from djoser.views import TokenDestroyView  # type: ignore[import-untyped]
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from custom_auth.jwt_cookie.constants import REFRESH_TOKEN_COOKIE_KEY
class JWTTokenLogoutView(TokenDestroyView):  # type: ignore[misc]
    def post(self, request: Request) -> Response:
        response = super().post(request)

        raw_refresh_token = request.COOKIES.get(REFRESH_TOKEN_COOKIE_KEY)
        if raw_refresh_token:
            refresh_token = RefreshToken(raw_refresh_token)
            refresh_token.blacklist()

        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response