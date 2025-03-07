from djoser.views import TokenDestroyView  # type: ignore[import-untyped]
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class JWTTokenLogoutView(TokenDestroyView):  # type: ignore[misc]
    def post(self, request: Request) -> Response:
        response = super().post(request)
        if isinstance(jwt_token := request.auth, (AccessToken, RefreshToken)):
            jwt_token.blacklist()
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
        return response  # type: ignore[no-any-return]
