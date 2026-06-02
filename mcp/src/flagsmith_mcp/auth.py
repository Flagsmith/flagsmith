from collections.abc import Generator

import httpx
from fastmcp.server.dependencies import get_http_headers


class FlagsmithAuth(httpx.Auth):
    def __init__(self, global_master_api_key: str | None = None) -> None:
        self._global_master_api_key = global_master_api_key

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        if "authorization" not in request.headers:
            # Prefer the caller's forwarded MCP `--header`; fall back to the
            # server's own static token (the only credential under stdio).
            forwarded = get_http_headers(include={"authorization"})
            if (
                authorization := forwarded.get("authorization")
                or self._global_authorization_value()
            ):
                request.headers["authorization"] = authorization
        yield request

    def _global_authorization_value(self) -> str | None:
        if self._global_master_api_key:
            return f"Api-Key {self._global_master_api_key}"
        return None
