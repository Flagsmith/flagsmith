import time
from collections.abc import Sequence

import mcp.types as mt
import pydantic_core
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.base import Tool, ToolResult
from prometheus_client import Counter, Gauge, Histogram

from flagsmith_mcp.errors import upstream_status_code

flagsmith_mcp_tool_call_duration_seconds = Histogram(
    "flagsmith_mcp_tool_call_duration_seconds",
    "Time spent serving an MCP tool call, including the upstream "
    "Flagsmith API request.",
    labelnames=["tool", "status"],
)
flagsmith_mcp_tool_result_bytes = Histogram(
    "flagsmith_mcp_tool_result_bytes",
    "Serialised size of a tool call result's text content and "
    "structuredContent. Helps approximate the call's token cost: clients "
    "render either or both into the agent's context.",
    labelnames=["tool", "content"],
    buckets=(256, 1024, 4096, 16384, 65536, 262144, 1048576, float("inf")),
)
flagsmith_mcp_tool_call_upstream_errors = Counter(
    "flagsmith_mcp_tool_call_upstream_errors",
    "Error responses the Flagsmith API returned to an MCP tool call. A 4xx "
    "reflects the caller's credential, arguments or target rather than a "
    "fault in this server; watch it here, as these are not sent to Sentry.",
    labelnames=["tool", "status_code"],
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
        except Exception as exc:
            flagsmith_mcp_tool_call_duration_seconds.labels(
                tool=tool, status="error"
            ).observe(time.perf_counter() - start)
            if (status_code := upstream_status_code(exc)) is not None:
                flagsmith_mcp_tool_call_upstream_errors.labels(
                    tool=tool, status_code=str(status_code)
                ).inc()
            raise
        flagsmith_mcp_tool_call_duration_seconds.labels(
            tool=tool, status="success"
        ).observe(time.perf_counter() - start)
        # Text blocks already hold the serialised payload; structuredContent
        # costs one compact dump, matching its wire encoding.
        unstructured_bytes = sum(
            len(block.text.encode())
            for block in result.content
            if isinstance(block, mt.TextContent)
        )
        structured_bytes = (
            len(pydantic_core.to_json(result.structured_content, fallback=str))
            if result.structured_content is not None
            else 0
        )
        for content, size in (
            ("unstructured", unstructured_bytes),
            ("structured", structured_bytes),
        ):
            flagsmith_mcp_tool_result_bytes.labels(
                tool=tool,
                content=content,
            ).observe(size)
        return result

    async def on_list_tools(
        self,
        context: MiddlewareContext[mt.ListToolsRequest],
        call_next: CallNext[mt.ListToolsRequest, Sequence[Tool]],
    ) -> Sequence[Tool]:
        tools = await call_next(context)
        flagsmith_mcp_tool_catalogue_bytes.set(
            len(
                pydantic_core.to_json(
                    [
                        tool.to_mcp_tool().model_dump(exclude_none=True, by_alias=True)
                        for tool in tools
                    ]
                )
            )
        )
        return tools
