from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import inflection
import structlog
from opentelemetry import baggage, trace
from opentelemetry import context as otel_context
from opentelemetry._logs import SeverityNumber
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.exporter.otlp.proto.http._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.textmap import TextMapPropagator
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)

_SEVERITY_MAP: dict[str, SeverityNumber] = {
    "debug": SeverityNumber.DEBUG,
    "info": SeverityNumber.INFO,
    "warning": SeverityNumber.WARN,
    "error": SeverityNumber.ERROR,
    "critical": SeverityNumber.FATAL,
}

_RESERVED_KEYS = frozenset({"event", "level", "timestamp", "logger"})

_resource: Resource | None = None


def _get_resource() -> Resource:
    global _resource
    if _resource is None:
        raise RuntimeError(
            "OTel resource not initialised — call init_resource() first."
        )
    return _resource


def init_resource(*, service_name: str) -> None:
    """Initialise the shared OTel Resource. Must be called before other setup."""
    global _resource
    _resource = Resource.create({"service.name": service_name})


class StructlogOTelProcessor:
    """A structlog processor that emits log records to OpenTelemetry.

    Sits in the processor chain *before* the final renderer so that
    only structlog-originated logs reach OTel.  Passes the event_dict
    through unchanged so downstream processors (console/JSON renderers)
    still work normally.
    """

    def __init__(self, logger_provider: LoggerProvider) -> None:
        self._logger = logger_provider.get_logger(__name__)

    def __call__(
        self,
        logger: structlog.types.WrappedLogger,
        method_name: str,
        event_dict: dict[str, Any],
    ) -> dict[str, Any]:
        level = event_dict.get("level", method_name)
        severity_number = _SEVERITY_MAP.get(level, SeverityNumber.INFO)

        attributes = {
            k.replace("__", "."): _serialise_value(v)
            for k, v in event_dict.items()
            if k not in _RESERVED_KEYS
        }

        # Copy W3C baggage entries into log attributes so downstream
        # exporters (e.g. Amplitude) can access them.
        ctx = otel_context.get_current()
        for key, value in baggage.get_all(ctx).items():
            attributes[key] = str(value)

        body = event_dict.get("event", "")
        event_name = inflection.underscore(body)
        logger_name = event_dict.get("logger")
        if logger_name:
            event_name = f"{logger_name}.{event_name}"

        self._logger.emit(
            timestamp=int(datetime.now(timezone.utc).timestamp() * 1e9),
            context=otel_context.get_current(),
            severity_text=level,
            severity_number=severity_number,
            body=body,
            event_name=event_name,
            attributes=attributes,
        )
        return event_dict


def _serialise_value(value: object) -> str | int | float | bool:
    """Coerce a value to an OTel-attribute-compatible type."""
    if isinstance(value, (bool, str, int, float)):
        return value
    return json.dumps(value, default=str)


def build_otel_provider(*, endpoint: str) -> LoggerProvider:
    """Create and configure an OTel LoggerProvider with OTLP/HTTP export."""
    provider = LoggerProvider(resource=_get_resource())
    exporter = OTLPLogExporter(endpoint=endpoint)
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    return provider


def setup_tracing(*, endpoint: str, service_name: str | None = None) -> None:
    """Set up OTel distributed tracing with Django instrumentation.

    Configures a TracerProvider with OTLP/HTTP export and W3C
    trace context + baggage propagation. Instruments Django so
    that every request creates a span with the incoming trace
    context (including baggage from the frontend).

    Must be called *before* Django's WSGI app is created.
    If ``service_name`` is provided, creates its own Resource;
    otherwise uses the shared one from ``init_resource()``.
    """
    resource = (
        Resource.create({"service.name": service_name})
        if service_name
        else _get_resource()
    )
    tracer_provider = TracerProvider(resource=resource)

    span_exporter = OTLPSpanExporter(endpoint=endpoint)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))

    trace.set_tracer_provider(tracer_provider)

    propagator: TextMapPropagator = CompositePropagator(
        [
            TraceContextTextMapPropagator(),
            W3CBaggagePropagator(),
        ]
    )
    set_global_textmap(propagator)

    DjangoInstrumentor().instrument()
