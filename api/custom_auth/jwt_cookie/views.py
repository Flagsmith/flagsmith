from djoser.views import TokenDestroyView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import SlidingToken


class TokenDestroyJWTSlidingBlacklistView(TokenDestroyView):
    def post(self, request: Request) -> Response:
        if isinstance(request.auth, SlidingToken):
            request.auth.blacklist()
        return super().post(request)
