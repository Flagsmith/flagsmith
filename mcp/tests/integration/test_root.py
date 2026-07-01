import httpx
import pytest

from flagsmith_mcp import constants

PRM_PATH = "/.well-known/oauth-protected-resource"


async def test_root__browser_accept__redirects_to_docs(
    http_client: httpx.AsyncClient,
) -> None:
    # When a browser (Accept: text/html) opens the bare server URL
    response = await http_client.get(
        "/", headers={"Accept": "text/html,application/xhtml+xml"}
    )

    # Then it is redirected to the MCP docs
    assert response.status_code == 302
    assert response.headers["location"] == constants.MCP_DOCS_URL


@pytest.mark.parametrize("method", ["GET", "POST"])
async def test_root__non_browser_request__dispatched_to_mcp_handler(
    http_client: httpx.AsyncClient,
    method: str,
) -> None:
    # When an MCP client hits the bare URL (no `/mcp` suffix, no credential)
    response = await http_client.request(
        method,
        "/",
        headers={"Accept": "application/json, text/event-stream"},
    )

    # Then the request reaches the MCP handler, which gates on the missing
    # credential and points the client at the protected-resource metadata
    assert response.status_code == 401
    assert PRM_PATH in response.headers["www-authenticate"]
