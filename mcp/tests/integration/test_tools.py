from typing import Any

import openapi_pydantic as openapi
import pytest
from fastmcp import Client
from fastmcp.client.transports import FastMCPTransport


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


async def test_tools_list__mcp_tagged_routes__returns_tool_catalogue(
    client: Client[FastMCPTransport],
) -> None:
    """https://gofastmcp.com/integrations/openapi#route-mapping"""
    # When
    tools = await client.list_tools()

    # Then
    assert {tool.name for tool in tools} == {"list_environments", "delete_environment"}


async def test_tool__from_get_route__annotates_read_only(
    client: Client[FastMCPTransport],
) -> None:
    """https://modelcontextprotocol.io/specification/2025-06-18/server/tools#tool-annotations"""
    # Given
    tools = {tool.name: tool for tool in await client.list_tools()}

    # When
    annotations = tools["list_environments"].annotations

    # Then
    assert annotations is not None
    assert annotations.readOnlyHint is True


async def test_tool__from_delete_route__annotates_destructive(
    client: Client[FastMCPTransport],
) -> None:
    """https://modelcontextprotocol.io/specification/2025-06-18/server/tools#tool-annotations"""
    # Given
    tools = {tool.name: tool for tool in await client.list_tools()}

    # When
    annotations = tools["delete_environment"].annotations

    # Then
    assert annotations is not None
    assert annotations.readOnlyHint is False
    assert annotations.destructiveHint is True
