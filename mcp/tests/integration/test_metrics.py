import httpx
import pytest
from fastmcp import Client
from fastmcp.client.transports import FastMCPTransport
from fastmcp.exceptions import ToolError
from prometheus_client import REGISTRY
from respx import MockRouter


async def test_metrics__successful_tool_call__records_duration_and_result_size(
    client: Client[FastMCPTransport],
    http_client: httpx.AsyncClient,
    respx_mock: MockRouter,
) -> None:
    # Given
    respx_mock.get("https://api.flagsmith.com/environments/").respond(
        json={"results": []}
    )
    duration_labels = {"tool": "list_environments", "status": "success"}
    result_labels = {"tool": "list_environments"}
    duration_count_before = (
        REGISTRY.get_sample_value(
            "flagsmith_mcp_tool_call_duration_seconds_count", duration_labels
        )
        or 0.0
    )
    result_count_before = (
        REGISTRY.get_sample_value(
            "flagsmith_mcp_tool_result_bytes_count", result_labels
        )
        or 0.0
    )

    # When
    await client.call_tool("list_environments", {})
    response = await http_client.get("/metrics")

    # Then
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert (
        REGISTRY.get_sample_value(
            "flagsmith_mcp_tool_call_duration_seconds_count", duration_labels
        )
        == duration_count_before + 1
    )
    assert (
        REGISTRY.get_sample_value(
            "flagsmith_mcp_tool_result_bytes_count", result_labels
        )
        == result_count_before + 1
    )
    result_bytes_sum = REGISTRY.get_sample_value(
        "flagsmith_mcp_tool_result_bytes_sum", result_labels
    )
    assert result_bytes_sum is not None
    assert result_bytes_sum > 0


async def test_metrics__failing_tool_call__records_error_duration_only(
    client: Client[FastMCPTransport],
    respx_mock: MockRouter,
) -> None:
    # Given
    respx_mock.get("https://api.flagsmith.com/environments/").respond(status_code=502)
    duration_labels = {"tool": "list_environments", "status": "error"}
    result_labels = {"tool": "list_environments"}
    duration_count_before = (
        REGISTRY.get_sample_value(
            "flagsmith_mcp_tool_call_duration_seconds_count", duration_labels
        )
        or 0.0
    )
    result_count_before = REGISTRY.get_sample_value(
        "flagsmith_mcp_tool_result_bytes_count", result_labels
    )

    # When
    with pytest.raises(ToolError):
        await client.call_tool("list_environments", {})

    # Then
    assert (
        REGISTRY.get_sample_value(
            "flagsmith_mcp_tool_call_duration_seconds_count", duration_labels
        )
        == duration_count_before + 1
    )
    assert (
        REGISTRY.get_sample_value(
            "flagsmith_mcp_tool_result_bytes_count", result_labels
        )
        == result_count_before
    )


async def test_metrics__tools_list__records_catalogue_size(
    client: Client[FastMCPTransport],
) -> None:
    # Given the server started via the client fixture
    # When
    tools = await client.list_tools()

    # Then a catalogue of two tools weighs at least a name and a schema each
    assert tools
    catalogue_bytes = REGISTRY.get_sample_value("flagsmith_mcp_tool_catalogue_bytes")
    assert catalogue_bytes is not None
    assert catalogue_bytes > len(tools) * 50
