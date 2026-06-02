from collections.abc import AsyncIterator
from typing import Any

import openapi_pydantic as openapi
import pytest
from fastmcp import Client, FastMCP
from fastmcp.client.transports import FastMCPTransport

from flagsmith_mcp import config, create_server
from flagsmith_mcp import server as server_module


@pytest.fixture
def openapi_spec() -> dict[str, Any]:
    ok = openapi.Response(description="OK")
    spec = openapi.OpenAPI(
        info=openapi.Info(title="Flagsmith API", version="1.0.0"),
        paths={
            "/environments/": openapi.PathItem(
                get=openapi.Operation(
                    operationId="list_environments", tags=["mcp"], responses={"200": ok}
                ),
            ),
            "/environments/{id}/": openapi.PathItem(
                delete=openapi.Operation(
                    operationId="delete_environment",
                    tags=["mcp"],
                    responses={"200": ok},
                ),
            ),
            "/internal/": openapi.PathItem(
                get=openapi.Operation(
                    operationId="internal_only", responses={"200": ok}
                ),
            ),
        },
    )
    return spec.model_dump(by_alias=True, exclude_none=True, mode="json")


@pytest.fixture
def server(
    monkeypatch: pytest.MonkeyPatch,
    openapi_spec: dict[str, Any],
) -> FastMCP:
    monkeypatch.setenv("FLAGSMITH_API_URL", "https://flagsmith.example.com")
    monkeypatch.setattr(server_module, "_fetch_spec", lambda: openapi_spec)
    return create_server(config.Settings())


@pytest.fixture
async def client(server: FastMCP) -> AsyncIterator[Client[FastMCPTransport]]:
    async with Client(transport=server) as connected:
        yield connected
