from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import SlidingToken


class JWTSlidingTokenLogoutView(APIView):
    """
    This view only invalidates the JWT cookie.
    Currently, for clients which use token authentication, it's a no-op view.
    """

    def post(self, request: Request) -> Response:
        if isinstance(request.auth, SlidingToken):
            request.auth.blacklist()
        return Response(status=HTTP_204_NO_CONTENT)
