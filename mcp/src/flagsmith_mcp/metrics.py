import time

import mcp.types as mt
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.base import ToolResult
from prometheus_client import Histogram

TOOL_CALL_DURATION_SECONDS = Histogram(
    "flagsmith_mcp_tool_call_duration_seconds",
    "Time spent serving an MCP tool call, including the upstream "
    "Flagsmith API request.",
    labelnames=["tool", "status"],
)
TOOL_RESULT_BYTES = Histogram(
    "flagsmith_mcp_tool_result_bytes",
    "Serialised size of a successful MCP tool call result. A proxy for "
    "the token cost a tool call incurs on the calling agent's context.",
    labelnames=["tool"],
    buckets=(256, 1024, 4096, 16384, 65536, 262144, 1048576, float("inf")),
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
            TOOL_CALL_DURATION_SECONDS.labels(tool=tool, status="error").observe(
                time.perf_counter() - start
            )
            raise
        TOOL_CALL_DURATION_SECONDS.labels(tool=tool, status="success").observe(
            time.perf_counter() - start
        )
        TOOL_RESULT_BYTES.labels(tool=tool).observe(
            len(result.model_dump_json(exclude_none=True).encode())
        )
        return result
