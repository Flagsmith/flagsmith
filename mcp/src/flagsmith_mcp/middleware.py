from starlette.datastructures import Headers
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from flagsmith_mcp import constants


class RootRouterMiddleware:
    """Make the bare server URL usable.

    Both MCP clients that drop the ``/mcp`` suffix and humans who open the URL
    in a browser land on ``/``. Browsers (``Accept: text/html``) are redirected
    to the docs; every other request is dispatched to the MCP handler so the
    bare URL works as an endpoint in its own right. Requests to any other path
    pass through untouched.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        docs_url: str = constants.MCP_DOCS_URL,
        mcp_path: str = constants.STREAMABLE_HTTP_PATH,
    ) -> None:
        self.app = app
        self.docs_url = docs_url
        self.mcp_path = mcp_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"] == "/":
            if "text/html" in Headers(scope=scope).get("accept", ""):
                response = RedirectResponse(self.docs_url, status_code=302)
                await response(scope, receive, send)
                return
            scope = {
                **scope,
                "path": self.mcp_path,
                "raw_path": self.mcp_path.encode(),
            }
        await self.app(scope, receive, send)
