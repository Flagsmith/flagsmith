from djoser.views import TokenDestroyView  # type: ignore[import-untyped]
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import SlidingToken

from custom_auth.jwt_cookie.constants import JWT_SLIDING_COOKIE_KEY


class JWTSlidingTokenLogoutView(TokenDestroyView):  # type: ignore[misc]
    def post(self, request: Request) -> Response:
        response = super().post(request)
        if isinstance(jwt_token := request.auth, SlidingToken):
            jwt_token.blacklist()
            response.delete_cookie(JWT_SLIDING_COOKIE_KEY)
        return response  # type: ignore[no-any-return]
