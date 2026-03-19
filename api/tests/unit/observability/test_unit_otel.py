from typing import Any
from unittest.mock import MagicMock

import pytest
from opentelemetry._logs import SeverityNumber
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import (
    InMemoryLogRecordExporter,
    SimpleLogRecordProcessor,
)
from opentelemetry.sdk.resources import Resource

from observability.otel import StructlogOTelProcessor, build_otel_provider


@pytest.fixture()
def otel_exporter() -> InMemoryLogRecordExporter:
    return InMemoryLogRecordExporter()


@pytest.fixture()
def processor(otel_exporter: InMemoryLogRecordExporter) -> StructlogOTelProcessor:
    provider = LoggerProvider(
        resource=Resource.create({"service.name": "test"}),
    )
    provider.add_log_record_processor(SimpleLogRecordProcessor(otel_exporter))
    return StructlogOTelProcessor(provider)


def test_build_otel_provider__valid_config__returns_logger_provider() -> None:
    # Given
    endpoint = "http://localhost:4318/v1/logs"
    service_name = "flagsmith-api-test"

    # When
    provider = build_otel_provider(
        endpoint=endpoint,
        service_name=service_name,
    )

    # Then
    assert isinstance(provider, LoggerProvider)


def test_StructlogOTelProcessor__event_with_logger_name__emits_namespaced_record(
    processor: StructlogOTelProcessor,
    otel_exporter: InMemoryLogRecordExporter,
) -> None:
    # Given
    event_dict: dict[str, Any] = {
        "event": "scan.created",
        "level": "info",
        "timestamp": "2025-01-01T00:00:00Z",
        "logger": "code_references",
        "organisation__id": 42,
        "code_references__count": 3,
    }

    # When
    result = processor(MagicMock(), "info", event_dict)

    # Then
    assert result is event_dict, "Processor must pass event_dict through"

    records = otel_exporter.get_finished_logs()
    assert len(records) == 1

    log_record = records[0].log_record
    assert log_record.body == "scan.created"
    assert log_record.event_name == "code_references.scan.created"
    assert log_record.severity_text == "info"
    assert log_record.severity_number == SeverityNumber.INFO
    assert log_record.attributes["organisation.id"] == 42
    assert log_record.attributes["code_references.count"] == 3
    assert "event" not in log_record.attributes
    assert "level" not in log_record.attributes
    assert "timestamp" not in log_record.attributes
    assert "logger" not in log_record.attributes


def test_StructlogOTelProcessor__kebab_case_event__normalises_to_underscores(
    processor: StructlogOTelProcessor,
    otel_exporter: InMemoryLogRecordExporter,
) -> None:
    # Given
    event_dict: dict[str, Any] = {
        "event": "scan-created",
        "level": "info",
        "logger": "code_references",
    }

    # When
    processor(MagicMock(), "info", event_dict)

    # Then
    log_record = otel_exporter.get_finished_logs()[0].log_record
    assert log_record.body == "scan-created"
    assert log_record.event_name == "code_references.scan_created"


def test_StructlogOTelProcessor__no_logger_name__uses_event_as_event_name(
    processor: StructlogOTelProcessor,
    otel_exporter: InMemoryLogRecordExporter,
) -> None:
    # Given
    event_dict: dict[str, Any] = {
        "event": "some-event",
        "level": "info",
    }

    # When
    processor(MagicMock(), "info", event_dict)

    # Then
    log_record = otel_exporter.get_finished_logs()[0].log_record
    assert log_record.body == "some-event"
    assert log_record.event_name == "some_event"


def test_StructlogOTelProcessor__dunder_attributes__converts_to_dots(
    processor: StructlogOTelProcessor,
    otel_exporter: InMemoryLogRecordExporter,
) -> None:
    # Given
    event_dict: dict[str, Any] = {
        "event": "test",
        "level": "info",
        "organisation__id": 1,
        "feature__count": 5,
        "code_references__count": 3,
    }

    # When
    processor(MagicMock(), "info", event_dict)

    # Then
    attrs = otel_exporter.get_finished_logs()[0].log_record.attributes
    assert attrs["organisation.id"] == 1
    assert attrs["feature.count"] == 5
    assert attrs["code_references.count"] == 3


def test_StructlogOTelProcessor__single_underscore_attributes__left_unchanged(
    processor: StructlogOTelProcessor,
    otel_exporter: InMemoryLogRecordExporter,
) -> None:
    # Given
    event_dict: dict[str, Any] = {
        "event": "test",
        "level": "info",
        "simple_attr": "value",
        "issues_created_count": 7,
    }

    # When
    processor(MagicMock(), "info", event_dict)

    # Then
    attrs = otel_exporter.get_finished_logs()[0].log_record.attributes
    assert attrs["simple_attr"] == "value"
    assert attrs["issues_created_count"] == 7


def test_StructlogOTelProcessor__non_primitive_attributes__serialises_to_json(
    processor: StructlogOTelProcessor,
    otel_exporter: InMemoryLogRecordExporter,
) -> None:
    # Given
    event_dict: dict[str, Any] = {
        "event": "test-event",
        "level": "info",
        "nested": {"key": "value"},
        "items": [1, 2, 3],
    }

    # When
    processor(MagicMock(), "info", event_dict)

    # Then
    attrs = otel_exporter.get_finished_logs()[0].log_record.attributes
    assert attrs["nested"] == '{"key": "value"}'
    assert attrs["items"] == "[1, 2, 3]"


@pytest.mark.parametrize(
    "level, expected_severity",
    [
        ("debug", SeverityNumber.DEBUG),
        ("info", SeverityNumber.INFO),
        ("warning", SeverityNumber.WARN),
        ("error", SeverityNumber.ERROR),
        ("critical", SeverityNumber.FATAL),
    ],
)
def test_StructlogOTelProcessor__severity_level__maps_correctly(
    processor: StructlogOTelProcessor,
    otel_exporter: InMemoryLogRecordExporter,
    level: str,
    expected_severity: SeverityNumber,
) -> None:
    # Given
    event_dict: dict[str, Any] = {"event": "test", "level": level}

    # When
    processor(MagicMock(), level, event_dict)

    # Then
    log_record = otel_exporter.get_finished_logs()[0].log_record
    assert log_record.severity_number == expected_severity
