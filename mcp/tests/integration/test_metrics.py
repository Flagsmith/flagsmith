import httpx
import pytest
from fastmcp import Client
from fastmcp.client.transports import FastMCPTransport
from fastmcp.exceptions import ToolError
from prometheus_client import REGISTRY
from respx import MockRouter


def _sample(name: str, labels: dict[str, str]) -> float:
    return REGISTRY.get_sample_value(name, labels) or 0.0


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
    duration_count_before = _sample(
        "flagsmith_mcp_tool_call_duration_seconds_count", duration_labels
    )
    result_count_before = _sample(
        "flagsmith_mcp_tool_result_bytes_count", result_labels
    )

    # When
    await client.call_tool("list_environments", {})
    response = await http_client.get("/metrics")

    # Then
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert (
        _sample("flagsmith_mcp_tool_call_duration_seconds_count", duration_labels)
        == duration_count_before + 1
    )
    assert (
        _sample("flagsmith_mcp_tool_result_bytes_count", result_labels)
        == result_count_before + 1
    )
    assert _sample("flagsmith_mcp_tool_result_bytes_sum", result_labels) > 0


async def test_metrics__failing_tool_call__records_error_duration_only(
    client: Client[FastMCPTransport],
    respx_mock: MockRouter,
) -> None:
    # Given
    respx_mock.get("https://api.flagsmith.com/environments/").respond(status_code=502)
    duration_labels = {"tool": "list_environments", "status": "error"}
    result_labels = {"tool": "list_environments"}
    duration_count_before = _sample(
        "flagsmith_mcp_tool_call_duration_seconds_count", duration_labels
    )
    result_count_before = _sample(
        "flagsmith_mcp_tool_result_bytes_count", result_labels
    )

    # When
    with pytest.raises(ToolError):
        await client.call_tool("list_environments", {})

    # Then
    assert (
        _sample("flagsmith_mcp_tool_call_duration_seconds_count", duration_labels)
        == duration_count_before + 1
    )
    assert (
        _sample("flagsmith_mcp_tool_result_bytes_count", result_labels)
        == result_count_before
    )
