from fastmcp.server.auth.auth import AccessToken, RemoteAuthProvider, TokenVerifier
from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from pydantic import AnyHttpUrl
from starlette.authentication import AuthCredentials, AuthenticationBackend
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import HTTPConnection

from flagsmith_mcp.constants import OAUTH_SCOPES


class _AnySchemeBackend(AuthenticationBackend):
    """Authenticates a request on the mere presence of an `Authorization`
    header, regardless of scheme (`Bearer` OAuth token or `Api-Key`). The
    credential is forwarded upstream verbatim and validated by the API."""

    async def authenticate(
        self, conn: HTTPConnection
    ) -> tuple[AuthCredentials, AuthenticatedUser] | None:
        if not (
            header := next(
                (
                    conn.headers.get(k)
                    for k in conn.headers
                    if k.lower() == "authorization"
                ),
                None,
            )
        ):
            return None

        token = header.split(" ", 1)[-1]
        access = AccessToken(
            token=token, client_id="flagsmith-mcp", scopes=OAUTH_SCOPES
        )
        return AuthCredentials(OAUTH_SCOPES), AuthenticatedUser(access)


class FlagsmithResourceAuth(RemoteAuthProvider):
    """OAuth 2.0 protected resource for HTTP transport.

    Serves Protected Resource Metadata (RFC 9728) pointing at the Flagsmith
    authorization server and returns 401 + `WWW-Authenticate` when a request
    carries no credential, so MCP clients can discover and complete the OAuth
    flow. Any `Authorization` header is accepted and passed through — the API
    validates it (no introspection here).
    """

    def __init__(self, *, resource_url: str, authorization_server: str) -> None:
        token_verifier = TokenVerifier(
            required_scopes=[]
        )  # never consulted — introspection done by Core API.
        super().__init__(
            token_verifier=token_verifier,
            authorization_servers=[AnyHttpUrl(authorization_server)],
            base_url=resource_url,
            scopes_supported=OAUTH_SCOPES,
        )

    def _get_resource_url(self, path: str | None = None) -> AnyHttpUrl | None:
        # Advertise the server origin as the protected resource
        # to enable client registration for both the root path and the /mcp path
        return super()._get_resource_url(None)

    def get_middleware(self) -> list[Middleware]:
        return [
            Middleware(AuthenticationMiddleware, backend=_AnySchemeBackend()),
            Middleware(AuthContextMiddleware),
        ]
