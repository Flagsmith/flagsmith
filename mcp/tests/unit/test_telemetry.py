import os

from common.core.otel import add_otel_trace_context
from pytest_mock import MockerFixture

from flagsmith_mcp import config, telemetry


def test_setup_telemetry__no_otlp_endpoint__configures_logging_only(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.dict(os.environ, {}, clear=True)
    setup_logging_mock = mocker.patch.object(telemetry, "setup_logging", autospec=True)
    set_tracer_provider_mock = mocker.patch(
        "flagsmith_mcp.telemetry.trace.set_tracer_provider", autospec=True
    )

    # When
    telemetry.setup_telemetry(config.Settings())

    # Then
    setup_logging_mock.assert_called_once_with(
        log_level="INFO",
        log_format="generic",
        application_loggers=telemetry.APPLICATION_LOGGERS,
        otel_processors=None,
    )
    set_tracer_provider_mock.assert_not_called()


def test_setup_telemetry__otlp_endpoint__exports_logs_and_traces(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.dict(os.environ, {}, clear=True)
    setup_logging_mock = mocker.patch.object(telemetry, "setup_logging", autospec=True)
    set_tracer_provider_mock = mocker.patch(
        "flagsmith_mcp.telemetry.trace.set_tracer_provider", autospec=True
    )
    build_otel_log_provider_mock = mocker.patch.object(
        telemetry, "build_otel_log_provider", autospec=True
    )
    build_tracer_provider_mock = mocker.patch.object(
        telemetry, "build_tracer_provider", autospec=True
    )
    make_structlog_otel_processor_mock = mocker.patch.object(
        telemetry, "make_structlog_otel_processor", autospec=True
    )
    settings = config.Settings(
        otel_exporter_otlp_endpoint="http://collector:4318/",
        otel_service_name="flagsmith-mcp-test",
        log_level="DEBUG",
        log_format="json",
    )

    # When
    telemetry.setup_telemetry(settings)

    # Then
    build_otel_log_provider_mock.assert_called_once_with(
        endpoint="http://collector:4318/v1/logs",
        service_name="flagsmith-mcp-test",
    )
    build_tracer_provider_mock.assert_called_once_with(
        endpoint="http://collector:4318/v1/traces",
        service_name="flagsmith-mcp-test",
    )
    make_structlog_otel_processor_mock.assert_called_once_with(
        build_otel_log_provider_mock.return_value
    )
    set_tracer_provider_mock.assert_called_once_with(
        build_tracer_provider_mock.return_value
    )
    setup_logging_mock.assert_called_once_with(
        log_level="DEBUG",
        log_format="json",
        application_loggers=telemetry.APPLICATION_LOGGERS,
        otel_processors=[
            add_otel_trace_context,
            make_structlog_otel_processor_mock.return_value,
        ],
    )
