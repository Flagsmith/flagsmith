from collections.abc import Generator

import httpx
from fastmcp.server.dependencies import get_http_headers


class FlagsmithAuth(httpx.Auth):
    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        # Restore MCP --header, if present
        if "authorization" not in request.headers:
            forwarded = get_http_headers(include={"authorization"})
            if authorization := forwarded.get("authorization"):
                request.headers["authorization"] = authorization
        yield request
