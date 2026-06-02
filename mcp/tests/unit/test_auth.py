import httpx
from fastmcp.server.http import set_http_request
from starlette.requests import Request

from flagsmith_mcp import auth


def test_flagsmith_auth__header_in_http_request__forwards_to_upstream() -> None:
    # Given an inbound HTTP request carrying an Authorization header, exactly as
    # FastMCP's RequestContextMiddleware sets it under HTTP transport (--header)
    inbound = Request(
        {"type": "http", "headers": [(b"authorization", b"Api-Key caller")]}
    )
    upstream = httpx.Request("GET", "https://api.flagsmith.com/api/v1/organisations/")

    # When the upstream auth flow runs within that request context
    with set_http_request(inbound):
        next(auth.FlagsmithAuth().auth_flow(upstream))

    # Then the real get_http_headers picks it up and forwards it
    assert upstream.headers["authorization"] == "Api-Key caller"


def test_flagsmith_auth__no_http_request__leaves_upstream_unchanged() -> None:
    # Given no active HTTP request (e.g. stdio transport)
    upstream = httpx.Request("GET", "https://api.flagsmith.com/api/v1/organisations/")

    # When
    next(auth.FlagsmithAuth().auth_flow(upstream))

    # Then nothing is forwarded
    assert "authorization" not in upstream.headers


def test_flagsmith_auth__upstream_already_authorized__does_not_override() -> None:
    # Given an upstream request that already carries a credential, and an inbound
    # header that differs
    inbound = Request(
        {"type": "http", "headers": [(b"authorization", b"Api-Key context")]}
    )
    upstream = httpx.Request(
        "GET",
        "https://api.flagsmith.com/api/v1/organisations/",
        headers={"authorization": "Api-Key static"},
    )

    # When
    with set_http_request(inbound):
        next(auth.FlagsmithAuth().auth_flow(upstream))

    # Then the existing credential wins
    assert upstream.headers["authorization"] == "Api-Key static"
