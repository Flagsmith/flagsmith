from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastmcp import Client, FastMCP
from fastmcp.client.transports import FastMCPTransport
from openapi_pydantic import Info, OpenAPI

from flagsmith_mcp import create_server
from flagsmith_mcp import server as server_module


@pytest.fixture
def openapi_spec() -> dict[str, Any]:
    spec = OpenAPI(info=Info(title="Flagsmith API", version="1.0.0"), paths={})
    return spec.model_dump(by_alias=True, exclude_none=True, mode="json")


@pytest.fixture
def server(
    monkeypatch: pytest.MonkeyPatch,
    openapi_spec: dict[str, Any],
) -> FastMCP:
    monkeypatch.setenv("FLAGSMITH_API_URL", "https://flagsmith.example.com")
    monkeypatch.setattr(server_module, "_fetch_spec", lambda: openapi_spec)
    return create_server()


@pytest.fixture
async def client(server: FastMCP) -> AsyncIterator[Client[FastMCPTransport]]:
    async with Client(transport=server) as connected:
        yield connected
