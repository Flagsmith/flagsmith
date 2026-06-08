import pytest
from fastmcp import Client
from fastmcp.client.transports import FastMCPTransport
from fastmcp.exceptions import ToolError
from pytest_structlog import StructuredLogCapture
from respx import MockRouter


async def test_events__session_initialised__emits_session_opened(
    log: StructuredLogCapture,
    client: Client[FastMCPTransport],
) -> None:
    # Given the server started via the client fixture
    # When the session is initialised by the fixture
    # Then the client's self-declared identity is reported
    assert log.has(
        "session.opened",
        flagsmith__mcp__client__name="mcp",
        flagsmith__mcp__client__version="0.1.0",
    )


async def test_events__successful_tool_call__emits_tool_called(
    log: StructuredLogCapture,
    client: Client[FastMCPTransport],
    respx_mock: MockRouter,
) -> None:
    # Given
    respx_mock.get("https://api.flagsmith.com/environments/").respond(
        json={"results": []}
    )

    # When
    await client.call_tool("list_environments", {})

    # Then
    [event] = [e for e in log.events if e["event"] == "tool.called"]
    assert event == {
        "event": "tool.called",
        "level": "info",
        "tool__name": "list_environments",
        "flagsmith__mcp__client__name": "mcp",
        "flagsmith__mcp__client__version": "0.1.0",
        "status": "success",
    }


async def test_events__failing_tool_call__emits_tool_called_with_error_status(
    log: StructuredLogCapture,
    client: Client[FastMCPTransport],
    respx_mock: MockRouter,
) -> None:
    # Given
    respx_mock.get("https://api.flagsmith.com/environments/").respond(status_code=502)

    # When
    with pytest.raises(ToolError):
        await client.call_tool("list_environments", {})

    # Then
    [event] = [e for e in log.events if e["event"] == "tool.called"]
    assert event == {
        "event": "tool.called",
        "level": "info",
        "tool__name": "list_environments",
        "flagsmith__mcp__client__name": "mcp",
        "flagsmith__mcp__client__version": "0.1.0",
        "status": "error",
    }
