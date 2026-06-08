from fastmcp import Client
from fastmcp.client.transports import FastMCPTransport


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
