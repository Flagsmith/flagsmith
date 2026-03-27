from rest_framework.request import Request

from oauth2_provider.contrib.rest_framework import OAuth2Authentication  # type: ignore[import-untyped]


class OAuth2BearerTokenAuthentication(OAuth2Authentication):  # type: ignore[misc]
    """DOT's default OAuth2Authentication also reads the request body
    looking for an access_token, which consumes the stream and breaks
    views that need to read request.body.
    """

    def authenticate(self, request: Request) -> tuple[object, str] | None:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None
        return super().authenticate(request)  # type: ignore[return-value]
