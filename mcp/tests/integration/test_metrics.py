import httpx
import pytest
from common.test_tools import AssertMetricFixture
from fastmcp import Client
from fastmcp.client.transports import FastMCPTransport
from fastmcp.exceptions import ToolError
from prometheus_client import REGISTRY
from respx import MockRouter


async def test_metrics__successful_tool_call__records_duration_and_result_size(
    client: Client[FastMCPTransport],
    http_client: httpx.AsyncClient,
    respx_mock: MockRouter,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given
    respx_mock.get("https://api.flagsmith.com/environments/").respond(
        json={"results": []}
    )

    # When
    await client.call_tool("list_environments", {})
    response = await http_client.get("/metrics")

    # Then
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert_metric(
        name="flagsmith_mcp_tool_call_duration_seconds_count",
        labels={"tool": "list_environments", "status": "success"},
        value=1,
    )
    content_sums: dict[str, float] = {}
    for content in ("unstructured", "structured", "total"):
        assert_metric(
            name="flagsmith_mcp_tool_result_bytes_count",
            labels={"tool": "list_environments", "content": content},
            value=1,
        )
        content_sum = REGISTRY.get_sample_value(
            "flagsmith_mcp_tool_result_bytes_sum",
            {"tool": "list_environments", "content": content},
        )
        assert content_sum is not None
        content_sums[content] = content_sum
    assert content_sums["unstructured"] > 0
    assert content_sums["structured"] > 0
    assert (
        content_sums["total"]
        == content_sums["unstructured"] + content_sums["structured"]
    )


async def test_metrics__failing_tool_call__records_error_duration_only(
    client: Client[FastMCPTransport],
    respx_mock: MockRouter,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given
    respx_mock.get("https://api.flagsmith.com/environments/").respond(status_code=502)

    # When
    with pytest.raises(ToolError):
        await client.call_tool("list_environments", {})

    # Then
    assert_metric(
        name="flagsmith_mcp_tool_call_duration_seconds_count",
        labels={"tool": "list_environments", "status": "error"},
        value=1,
    )
    assert (
        REGISTRY.get_sample_value(
            "flagsmith_mcp_tool_result_bytes_count",
            {"tool": "list_environments", "content": "total"},
        )
        is None
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
