import httpx


def upstream_status_code(exc: BaseException | None) -> int | None:
    """The status of the Flagsmith API response that caused `exc`, if any.

    A failing tool call surfaces as a chain: httpx raises `HTTPStatusError`,
    FastMCP's OpenAPI provider re-raises it as `ValueError`, and the server
    wraps that in a `ToolError`. Walking the chain recovers the response that
    started it.
    """
    seen: set[int] = set()
    while exc is not None and id(exc) not in seen:
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code
        seen.add(id(exc))
        exc = exc.__cause__ or exc.__context__
    return None
