import httpx
import sentry_sdk
from common.core.logging import setup_logging
from common.core.otel import (
    add_otel_trace_context,
    build_otel_log_provider,
    build_tracer_provider,
    make_structlog_otel_processor,
)
from opentelemetry import baggage, trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor, TracerProvider
from sentry_sdk.types import Event, Hint
from structlog.typing import Processor

from flagsmith_mcp import config, constants
from flagsmith_mcp.errors import upstream_status_code
from flagsmith_mcp.events import get_client_info

APPLICATION_LOGGERS = ["flagsmith_mcp", "fastmcp", "mcp"]


class ClientInfoSpanProcessor(SpanProcessor):
    """Annotate started spans with this service's identity and the MCP
    client identity."""

    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        span.set_attribute("flagsmith.client.name", constants.FLAGSMITH_CLIENT_NAME)
        if (client_info := get_client_info()) is not None:
            span.set_attribute("flagsmith.mcp.client.name", client_info.name)
            span.set_attribute("flagsmith.mcp.client.version", client_info.version)


async def propagate_span_attributes(request: httpx.Request) -> None:
    span = trace.get_current_span()
    if not isinstance(span, ReadableSpan):
        return
    ctx: Context | None = None
    for key, value in (span.attributes or {}).items():
        ctx = baggage.set_baggage(key, str(value), context=ctx)
    if ctx is not None:
        W3CBaggagePropagator().inject(request.headers, context=ctx)


def setup_telemetry(settings: config.Settings) -> None:
    """Set up logging, exporting structlog events and traces to OpenTelemetry
    when an OTLP endpoint is configured."""
    otel_processors: list[Processor] | None = None
    if settings.otel_exporter_otlp_endpoint:
        endpoint = settings.otel_exporter_otlp_endpoint.rstrip("/")
        log_provider = build_otel_log_provider(
            endpoint=f"{endpoint}/v1/logs",
            service_name=settings.otel_service_name,
            protocol="http/protobuf",
        )
        otel_processors = [
            add_otel_trace_context,
            make_structlog_otel_processor(log_provider),
        ]
        tracer_provider = build_tracer_provider(
            endpoint=f"{endpoint}/v1/traces",
            service_name=settings.otel_service_name,
            protocol="http/protobuf",
        )
    else:
        # No exporter: spans stay in-process, but still feed the API
        # baggage propagation.
        tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(ClientInfoSpanProcessor())
    trace.set_tracer_provider(tracer_provider)
    setup_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
        application_loggers=APPLICATION_LOGGERS,
        otel_processors=otel_processors,
    )


def drop_upstream_client_errors(event: Event, hint: Hint) -> Event | None:
    """Discard errors that a 4xx from the Flagsmith API caused.

    A 4xx means the caller's credential, arguments or target were wrong. The
    server relayed that faithfully, and the client sees the error, so it is
    not a fault anyone can act on here — only noise that buries real ones.
    Server faults (5xx) and transport failures still report, and 4xx rates
    stay visible via `flagsmith_mcp_tool_call_upstream_errors_total`.
    """
    if (exc_info := hint.get("exc_info")) is None:
        return event
    status_code = upstream_status_code(exc_info[1])
    if status_code is not None and httpx.codes.is_client_error(status_code):
        return None
    return event


def setup_sentry(settings: config.Settings) -> None:
    """Initialise Sentry for error capture when a DSN is configured."""
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=str(settings.sentry_dsn),
        environment=settings.environment,
        before_send=drop_upstream_client_errors,
    )
