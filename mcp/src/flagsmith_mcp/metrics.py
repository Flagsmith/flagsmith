import json
import time
from collections.abc import Sequence

import mcp.types as mt
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.base import Tool, ToolResult
from prometheus_client import Gauge, Histogram

flagsmith_mcp_tool_call_duration_seconds = Histogram(
    "flagsmith_mcp_tool_call_duration_seconds",
    "Time spent serving an MCP tool call, including the upstream "
    "Flagsmith API request.",
    labelnames=["tool", "status"],
)
flagsmith_mcp_tool_result_bytes = Histogram(
    "flagsmith_mcp_tool_result_bytes",
    "Serialised size of a successful MCP tool call result. A proxy for "
    "the token cost a tool call incurs on the calling agent's context.",
    labelnames=["tool"],
    buckets=(256, 1024, 4096, 16384, 65536, 262144, 1048576, float("inf")),
)
flagsmith_mcp_tool_catalogue_bytes = Gauge(
    "flagsmith_mcp_tool_catalogue_bytes",
    "Serialised size of the tool catalogue returned by tools/list. A proxy "
    "for the token cost every MCP session pays before any tool is called.",
)


class PrometheusMiddleware(Middleware):
    """Record Prometheus metrics for MCP tool calls."""

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        tool = context.message.name
        start = time.perf_counter()
        try:
            result = await call_next(context)
        except Exception:
            flagsmith_mcp_tool_call_duration_seconds.labels(
                tool=tool, status="error"
            ).observe(time.perf_counter() - start)
            raise
        flagsmith_mcp_tool_call_duration_seconds.labels(
            tool=tool, status="success"
        ).observe(time.perf_counter() - start)
        flagsmith_mcp_tool_result_bytes.labels(tool=tool).observe(
            len(result.model_dump_json(exclude_none=True).encode())
        )
        return result

    async def on_list_tools(
        self,
        context: MiddlewareContext[mt.ListToolsRequest],
        call_next: CallNext[mt.ListToolsRequest, Sequence[Tool]],
    ) -> Sequence[Tool]:
        tools = await call_next(context)
        flagsmith_mcp_tool_catalogue_bytes.set(
            len(
                json.dumps(
                    [
                        tool.to_mcp_tool().model_dump(exclude_none=True, by_alias=True)
                        for tool in tools
                    ]
                ).encode()
            )
        )
        return tools
