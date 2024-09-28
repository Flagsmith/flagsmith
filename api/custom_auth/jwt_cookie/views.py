from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import SlidingToken

from custom_auth.jwt_cookie.constants import JWT_SLIDING_COOKIE_KEY


class JWTSlidingTokenLogoutView(APIView):
    """
    This view only invalidates the JWT cookie.
    Currently, for clients which use token authentication, it's a no-op view.
    """

    def post(self, request: Request) -> Response:
        response = Response(status=HTTP_204_NO_CONTENT)
        if isinstance(request.auth, SlidingToken):
            request.auth.blacklist()
            response.delete_cookie(JWT_SLIDING_COOKIE_KEY)
        return response
