from typing import Any
from unittest.mock import MagicMock

from opentelemetry._logs import SeverityNumber
from opentelemetry.sdk._logs import LoggerProvider

from observability.otel import StructlogOTelProcessor, build_otel_provider


def test_build_otel_provider__returns_configured_logger_provider() -> None:
    # When
    provider = build_otel_provider(
        endpoint="http://localhost:4318/v1/logs",
        service_name="flagsmith-api-test",
    )

    # Then
    assert isinstance(provider, LoggerProvider)


class TestStructlogOTelProcessor:
    def test___call____emits_log_record_with_structured_attributes(
        self,
    ) -> None:
        # Given
        mock_provider = MagicMock(spec=LoggerProvider)
        mock_otel_logger = MagicMock()
        mock_provider.get_logger.return_value = mock_otel_logger
        processor = StructlogOTelProcessor(mock_provider)

        event_dict: dict[str, Any] = {
            "event": "code-references-scan-created",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "organisation_id": 42,
            "code_references_count": 3,
        }

        # When
        result = processor(MagicMock(), "info", event_dict)

        # Then
        assert result is event_dict, "Processor must pass event_dict through"
        mock_otel_logger.emit.assert_called_once()

        kwargs = mock_otel_logger.emit.call_args.kwargs
        assert kwargs["body"] == "code-references-scan-created"
        assert kwargs["severity_text"] == "info"
        assert kwargs["severity_number"] == SeverityNumber.INFO
        assert kwargs["attributes"]["organisation_id"] == 42
        assert kwargs["attributes"]["code_references_count"] == 3
        assert "event" not in kwargs["attributes"]
        assert "level" not in kwargs["attributes"]
        assert "timestamp" not in kwargs["attributes"]

    def test___call____serialises_non_primitive_attributes_to_json(
        self,
    ) -> None:
        # Given
        mock_provider = MagicMock(spec=LoggerProvider)
        mock_otel_logger = MagicMock()
        mock_provider.get_logger.return_value = mock_otel_logger
        processor = StructlogOTelProcessor(mock_provider)

        event_dict: dict[str, Any] = {
            "event": "test-event",
            "level": "info",
            "nested": {"key": "value"},
            "items": [1, 2, 3],
        }

        # When
        processor(MagicMock(), "info", event_dict)

        # Then
        kwargs = mock_otel_logger.emit.call_args.kwargs
        assert kwargs["attributes"]["nested"] == '{"key": "value"}'
        assert kwargs["attributes"]["items"] == "[1, 2, 3]"

    def test___call____maps_severity_levels_correctly(self) -> None:
        # Given
        mock_provider = MagicMock(spec=LoggerProvider)
        mock_otel_logger = MagicMock()
        mock_provider.get_logger.return_value = mock_otel_logger
        processor = StructlogOTelProcessor(mock_provider)

        expected_mappings = {
            "debug": SeverityNumber.DEBUG,
            "info": SeverityNumber.INFO,
            "warning": SeverityNumber.WARN,
            "error": SeverityNumber.ERROR,
            "critical": SeverityNumber.FATAL,
        }

        for level, expected_severity in expected_mappings.items():
            mock_otel_logger.reset_mock()

            # When
            processor(
                MagicMock(),
                level,
                {"event": "test", "level": level},
            )

            # Then
            kwargs = mock_otel_logger.emit.call_args.kwargs
            assert kwargs["severity_number"] == expected_severity, (
                f"Level {level!r} should map to {expected_severity}"
            )
