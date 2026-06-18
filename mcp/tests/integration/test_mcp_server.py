import httpx
from fastmcp import Client
from fastmcp.client.transports import FastMCPTransport
from mcp.types import LATEST_PROTOCOL_VERSION


async def test_mcp_server__ping__returns_expected(
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


async def test_mcp_server__health__returns_ok(
    http_client: httpx.AsyncClient,
) -> None:
    # Given the server started via the client fixture
    # When
    response = await http_client.get("/health")

    # Then
    assert response.status_code == 200
    assert response.text == "OK"
