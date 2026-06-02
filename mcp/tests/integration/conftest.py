from collections.abc import AsyncIterator

import pytest
from fastmcp import Client, FastMCP
from fastmcp.client.transports import FastMCPTransport
from flagsmith_mcp import create_server
from openapi_pydantic import OpenAPI


@pytest.fixture
def openapi_spec() -> OpenAPI | None:
    return None


@pytest.fixture
def server(
    monkeypatch: pytest.MonkeyPatch,
    openapi_spec: OpenAPI | None,
) -> FastMCP:
    monkeypatch.setenv("FLAGSMITH_API_URL", "https://flagsmith.example.com/api/v1")
    return create_server(openapi_spec=openapi_spec)


@pytest.fixture
async def client(server: FastMCP) -> AsyncIterator[Client[FastMCPTransport]]:
    async with Client(transport=server) as connected:
        yield connected
