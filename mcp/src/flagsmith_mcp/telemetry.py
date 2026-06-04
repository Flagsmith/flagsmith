import mcp.types as mt
from common.core.logging import setup_logging
from common.core.otel import (
    add_otel_trace_context,
    build_otel_log_provider,
    build_tracer_provider,
    make_structlog_otel_processor,
)
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.base import ToolResult
from opentelemetry import baggage, trace
from opentelemetry import context as otel_context
from opentelemetry.context import Context
from opentelemetry.sdk.trace import Span, SpanProcessor
from structlog.typing import Processor

from flagsmith_mcp import config
from flagsmith_mcp.events import get_client_info

APPLICATION_LOGGERS = ["flagsmith_mcp", "fastmcp", "mcp"]


class ClientInfoSpanProcessor(SpanProcessor):
    """Annotate started spans with the MCP client's self-declared identity."""

    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        if (client_info := get_client_info()) is not None:
            span.set_attribute("flagsmith.client.name", client_info.name)
            span.set_attribute("flagsmith.client.version", client_info.version)


class BaggageMiddleware(Middleware):
    """Attach the tool name and client identity as W3C Baggage, propagated
    to the Flagsmith API by the instrumented upstream HTTP client."""

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        ctx = baggage.set_baggage("flagsmith.tool.name", context.message.name)
        if (client_info := get_client_info()) is not None:
            ctx = baggage.set_baggage(
                "flagsmith.client.name", client_info.name, context=ctx
            )
            ctx = baggage.set_baggage(
                "flagsmith.client.version", client_info.version, context=ctx
            )
        token = otel_context.attach(ctx)
        try:
            return await call_next(context)
        finally:
            otel_context.detach(token)


def setup_telemetry(settings: config.Settings) -> None:
    """Set up logging, exporting structlog events and traces to OpenTelemetry
    when an OTLP endpoint is configured."""
    otel_processors: list[Processor] | None = None
    if settings.otel_exporter_otlp_endpoint:
        endpoint = settings.otel_exporter_otlp_endpoint.rstrip("/")
        log_provider = build_otel_log_provider(
            endpoint=f"{endpoint}/v1/logs",
            service_name=settings.otel_service_name,
        )
        otel_processors = [
            add_otel_trace_context,
            make_structlog_otel_processor(log_provider),
        ]
        # Setting a global tracer provider also activates FastMCP's built-in
        # per-request server spans.
        tracer_provider = build_tracer_provider(
            endpoint=f"{endpoint}/v1/traces",
            service_name=settings.otel_service_name,
        )
        tracer_provider.add_span_processor(ClientInfoSpanProcessor())
        trace.set_tracer_provider(tracer_provider)
    setup_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
        application_loggers=APPLICATION_LOGGERS,
        otel_processors=otel_processors,
    )
