from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog
from opentelemetry import context as otel_context
from opentelemetry._logs import SeverityNumber
from opentelemetry.exporter.otlp.proto.http._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

_SEVERITY_MAP: dict[str, SeverityNumber] = {
    "debug": SeverityNumber.DEBUG,
    "info": SeverityNumber.INFO,
    "warning": SeverityNumber.WARN,
    "error": SeverityNumber.ERROR,
    "critical": SeverityNumber.FATAL,
}

_RESERVED_KEYS = frozenset({"event", "level", "timestamp"})


def _serialise_value(value: object) -> str | int | float | bool:
    """Coerce a value to an OTel-attribute-compatible type."""
    if isinstance(value, (bool, str, int, float)):
        return value
    return json.dumps(value, default=str)


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
            k: _serialise_value(v)
            for k, v in event_dict.items()
            if k not in _RESERVED_KEYS
        }

        self._logger.emit(
            timestamp=int(datetime.now(timezone.utc).timestamp() * 1e9),
            context=otel_context.get_current(),
            severity_text=level,
            severity_number=severity_number,
            body=event_dict.get("event", ""),
            attributes=attributes,
        )
        return event_dict


def build_otel_provider(
    *,
    endpoint: str,
    service_name: str,
) -> LoggerProvider:
    """Create and configure an OTel LoggerProvider with OTLP/HTTP export."""
    resource = Resource.create({"service.name": service_name})
    provider = LoggerProvider(resource=resource)
    exporter = OTLPLogExporter(endpoint=endpoint)
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    return provider
