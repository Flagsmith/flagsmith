import httpx
import pytest
from common.test_tools import SnapshotFixture
from fastmcp import Client
from fastmcp.client.transports import FastMCPTransport
from mcp.types import LATEST_PROTOCOL_VERSION
from prometheus_client import start_http_server
from respx import MockRouter


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


@pytest.mark.usefixtures("assert_metric")
def test_metrics_server__exposition__matches_snapshot(
    snapshot: SnapshotFixture,
    respx_mock: MockRouter,
) -> None:
    # Given a metrics server on an ephemeral port
    respx_mock.route(host="127.0.0.1").pass_through()
    server, thread = start_http_server(0)

    try:
        # When
        response = httpx.get(f"http://127.0.0.1:{server.server_port}/metrics")
    finally:
        server.shutdown()
        thread.join()

    # Then
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert snapshot() == "\n".join(
        line for line in response.text.splitlines() if "flagsmith_mcp" in line
    )
