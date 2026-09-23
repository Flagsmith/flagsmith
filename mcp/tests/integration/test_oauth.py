from collections.abc import AsyncIterator

import httpx
import pytest
from conftest import HTTPClientFactoryFixture
from fastmcp import FastMCP

from flagsmith_mcp import config
from flagsmith_mcp import server as server_module

PRM_PATH = "/.well-known/oauth-protected-resource"


@pytest.fixture
def server_with_flagsmith_api_token() -> FastMCP:
    return server_module.create_server(
        config.Settings(flagsmith_api_token="secret.token")
    )


@pytest.fixture
async def http_client_with_flagsmith_api_token(
    server_with_flagsmith_api_token: FastMCP,
    http_client_factory: HTTPClientFactoryFixture,
) -> AsyncIterator[httpx.AsyncClient]:
    async for client in http_client_factory(server_with_flagsmith_api_token):
        yield client


async def test_http_no_token__serves_protected_resource_metadata(
    http_client: httpx.AsyncClient,
) -> None:
    # Given OAuth discovery is active (server fixture: http, no static token)
    response = await http_client.get(PRM_PATH)

    # Then it advertises the Flagsmith AS and the mcp scope (RFC 9728), and the
    # resource is the server origin
    assert response.status_code == 200
    body = response.json()
    assert body["resource"] == "http://127.0.0.1:8000/"
    assert body["authorization_servers"] == ["https://api.flagsmith.com/"]
    assert body["scopes_supported"] == ["mcp"]


async def test_http_no_token__missing_authorization__401_points_at_prm(
    http_client: httpx.AsyncClient,
) -> None:
    # When a request reaches the MCP endpoint with no credential
    response = await http_client.get("/mcp")

    # Then it 401s (no API round-trip) and points the client at the PRM
    assert response.status_code == 401
    assert PRM_PATH in response.headers["www-authenticate"]


async def test_http_no_token__non_bearer_credential__accepted_by_gate(
    http_client: httpx.AsyncClient,
) -> None:
    # When a request carries a non-Bearer (Api-Key) credential
    response = await http_client.get(
        PRM_PATH, headers={"Authorization": "Api-Key ser.secret"}
    )

    # Then the gate authenticates it (scheme-agnostic); end-to-end pass-through
    # to the API is exercised against live SaaS.
    assert response.status_code == 200


async def test_http_static_token__no_oauth_resource(
    http_client_with_flagsmith_api_token: httpx.AsyncClient,
) -> None:
    # Given a static token (pure pass-through, OAuth disabled)
    response = await http_client_with_flagsmith_api_token.get(PRM_PATH)

    # Then no protected-resource metadata is served
    assert response.status_code == 404
