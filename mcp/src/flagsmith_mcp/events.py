import mcp.types as mt
import structlog
from fastmcp.server.dependencies import get_context
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.base import ToolResult

logger = structlog.get_logger("mcp")


def get_client_info() -> mt.Implementation | None:
    """The connected client's self-declared identity, captured by the
    session during initialize."""
    try:
        client_params = get_context().session.client_params
    except RuntimeError:
        return None
    if client_params is None:
        return None
    return client_params.clientInfo


class EventLoggingMiddleware(Middleware):
    """Emit structured product events for MCP sessions and tool calls."""

    async def on_initialize(
        self,
        context: MiddlewareContext[mt.InitializeRequest],
        call_next: CallNext[mt.InitializeRequest, mt.InitializeResult | None],
    ) -> mt.InitializeResult | None:
        result = await call_next(context)
        client_info = context.message.params.clientInfo
        logger.info(
            "session.opened",
            flagsmith__client__name=client_info.name,
            flagsmith__client__version=client_info.version,
        )
        return result

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        client_info = get_client_info()
        client_name = client_info.name if client_info else ""
        client_version = client_info.version if client_info else ""
        try:
            result = await call_next(context)
        except Exception:
            logger.info(
                "tool.called",
                tool__name=context.message.name,
                flagsmith__client__name=client_name,
                flagsmith__client__version=client_version,
                status="error",
            )
            raise
        logger.info(
            "tool.called",
            tool__name=context.message.name,
            flagsmith__client__name=client_name,
            flagsmith__client__version=client_version,
            status="success",
        )
        return result
