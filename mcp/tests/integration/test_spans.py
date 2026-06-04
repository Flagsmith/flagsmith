from fastmcp import Client
from fastmcp.client.transports import FastMCPTransport
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import SpanKind
from respx import MockRouter


async def test_spans__tool_call__annotated_with_client_identity(
    client: Client[FastMCPTransport],
    respx_mock: MockRouter,
    finished_spans: InMemorySpanExporter,
) -> None:
    # Given
    respx_mock.get("https://api.flagsmith.com/environments/").respond(
        json={"results": []}
    )

    # When
    await client.call_tool("list_environments", {})

    # Then the FastMCP server span carries the client's identity
    [span] = [
        s
        for s in finished_spans.get_finished_spans()
        if s.kind == SpanKind.SERVER and s.name == "tools/call list_environments"
    ]
    assert span.attributes is not None
    assert {
        "gen_ai.tool.name": "list_environments",
        "flagsmith.client.name": "mcp",
        "flagsmith.client.version": "0.1.0",
    }.items() <= dict(span.attributes).items()
