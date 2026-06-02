from fastmcp import Client
from fastmcp.client.transports import FastMCPTransport
from mcp.types import LATEST_PROTOCOL_VERSION


async def test_mcp_server__running__succeeds_health_check(
    client: Client[FastMCPTransport],
) -> None:
    """https://modelcontextprotocol.io/specification/2025-06-18/basic/utilities/ping"""
    # Given the server started via the client fixture
    # When
    healthy = await client.ping()

    # Then
    assert healthy is True


async def test_mcp_server__initialize__responds_per_protocol_version(
    client: Client[FastMCPTransport],
) -> None:
    """https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle"""
    # Given the server started via the client fixture
    # When
    result = client.initialize_result

    # Then
    assert result is not None
    assert result.protocolVersion == LATEST_PROTOCOL_VERSION
