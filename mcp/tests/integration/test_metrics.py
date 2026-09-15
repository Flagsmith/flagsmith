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
    respx_mock: MockRouter,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given
    respx_mock.get("https://api.flagsmith.com/environments/").respond(
        json={"results": []}
    )

    # When
    await client.call_tool("list_environments", {})

    # Then
    assert_metric(
        name="flagsmith_mcp_tool_call_duration_seconds_count",
        labels={"tool": "list_environments", "status": "success"},
        value=1,
    )
    for content in ("unstructured", "structured"):
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
        assert content_sum > 0


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
            {"tool": "list_environments", "content": "unstructured"},
        )
        is None
    )


async def test_metrics__upstream_client_error__counts_status_code(
    client: Client[FastMCPTransport],
    respx_mock: MockRouter,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given the Flagsmith API rejects the caller's credential
    respx_mock.get("https://api.flagsmith.com/environments/").respond(status_code=401)

    # When
    with pytest.raises(ToolError):
        await client.call_tool("list_environments", {})

    # Then the 4xx stays visible here, since Sentry no longer reports it
    assert_metric(
        name="flagsmith_mcp_tool_call_upstream_errors_total",
        labels={"tool": "list_environments", "status_code": "401"},
        value=1,
    )


async def test_metrics__transport_failure__counts_no_status_code(
    client: Client[FastMCPTransport],
    respx_mock: MockRouter,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given the Flagsmith API never answers, so there is no status to record
    respx_mock.get("https://api.flagsmith.com/environments/").mock(
        side_effect=httpx.ConnectTimeout("timed out")
    )

    # When
    with pytest.raises(ToolError):
        await client.call_tool("list_environments", {})

    # Then the duration is recorded, but the upstream error counter is not
    assert_metric(
        name="flagsmith_mcp_tool_call_duration_seconds_count",
        labels={"tool": "list_environments", "status": "error"},
        value=1,
    )
    assert not [
        sample
        for metric in REGISTRY.collect()
        if metric.name == "flagsmith_mcp_tool_call_upstream_errors"
        for sample in metric.samples
    ]


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
