from common.core.logging import setup_logging
from common.core.otel import (
    add_otel_trace_context,
    build_otel_log_provider,
    build_tracer_provider,
    make_structlog_otel_processor,
)
from opentelemetry import trace
from structlog.typing import Processor

from flagsmith_mcp import config

APPLICATION_LOGGERS = ["flagsmith_mcp", "fastmcp", "mcp"]


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
        trace.set_tracer_provider(
            build_tracer_provider(
                endpoint=f"{endpoint}/v1/traces",
                service_name=settings.otel_service_name,
            )
        )
    setup_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
        application_loggers=APPLICATION_LOGGERS,
        otel_processors=otel_processors,
    )
