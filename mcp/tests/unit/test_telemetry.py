import os

import httpx
from common.core.otel import add_otel_trace_context
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan
from pydantic import HttpUrl
from pytest_mock import MockerFixture

from flagsmith_mcp import config, constants, telemetry


def test_setup_telemetry__no_otlp_endpoint__spans_in_process_only(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.dict(os.environ, {}, clear=True)
    setup_logging_mock = mocker.patch.object(telemetry, "setup_logging", autospec=True)
    set_tracer_provider_mock = mocker.patch(
        "flagsmith_mcp.telemetry.trace.set_tracer_provider", autospec=True
    )
    build_tracer_provider_mock = mocker.patch.object(
        telemetry, "build_tracer_provider", autospec=True
    )
    tracer_provider_mock = mocker.patch.object(
        telemetry, "TracerProvider", autospec=True
    )

    # When
    telemetry.setup_telemetry(config.Settings())

    # Then logging is configured without OTel export...
    setup_logging_mock.assert_called_once_with(
        log_level="INFO",
        log_format="generic",
        application_loggers=telemetry.APPLICATION_LOGGERS,
        otel_processors=None,
    )
    # ...but spans still record in-process
    build_tracer_provider_mock.assert_not_called()
    set_tracer_provider_mock.assert_called_once_with(tracer_provider_mock.return_value)
    [span_processor] = (
        tracer_provider_mock.return_value.add_span_processor.call_args.args
    )
    assert isinstance(span_processor, telemetry.ClientInfoSpanProcessor)


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
    [span_processor] = (
        build_tracer_provider_mock.return_value.add_span_processor.call_args.args
    )
    assert isinstance(span_processor, telemetry.ClientInfoSpanProcessor)
    setup_logging_mock.assert_called_once_with(
        log_level="DEBUG",
        log_format="json",
        application_loggers=telemetry.APPLICATION_LOGGERS,
        otel_processors=[
            add_otel_trace_context,
            make_structlog_otel_processor_mock.return_value,
        ],
    )


def test_client_info_span_processor__outside_request_context__service_identity_only(
    mocker: MockerFixture,
) -> None:
    # Given no MCP request context
    span = mocker.Mock()

    # When
    telemetry.ClientInfoSpanProcessor().on_start(span)

    # Then
    span.set_attribute.assert_called_once_with(
        "flagsmith.client.name", constants.FLAGSMITH_CLIENT_NAME
    )


def test_setup_sentry__no_dsn__init_not_called(mocker: MockerFixture) -> None:
    # Given
    mocker.patch.dict(os.environ, {}, clear=True)
    sentry_sdk_mock = mocker.patch.object(telemetry, "sentry_sdk", autospec=True)
    empty_settings = config.Settings()

    # When
    telemetry.setup_sentry(empty_settings)

    # Then
    sentry_sdk_mock.init.assert_not_called()


def test_setup_sentry__dsn_set__initialises_error_capture(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.dict(os.environ, {}, clear=True)
    sentry_sdk_mock = mocker.patch.object(telemetry, "sentry_sdk", autospec=True)
    settings = config.Settings(
        sentry_dsn=HttpUrl("https://public@sentry.example/1"),
        environment="staging",
    )

    # When
    telemetry.setup_sentry(settings)

    # Then
    sentry_sdk_mock.init.assert_called_once_with(
        dsn="https://public@sentry.example/1",
        environment="staging",
    )


async def test_propagate_span_attributes__no_recording_span__headers_untouched() -> (
    None
):
    # Given no SDK span in the current context
    request = httpx.Request("GET", "https://api.flagsmith.com/")

    # When
    await telemetry.propagate_span_attributes(request)

    # Then
    assert "baggage" not in request.headers


async def test_propagate_span_attributes__span_without_attributes__headers_untouched(
    mocker: MockerFixture,
) -> None:
    # Given a recording span with no attributes
    span = mocker.Mock(spec=ReadableSpan)
    span.attributes = {}
    mocker.patch.object(trace, "get_current_span", return_value=span)

    # When
    request = httpx.Request("GET", "https://api.flagsmith.com/")
    await telemetry.propagate_span_attributes(request)

    # Then
    assert "baggage" not in request.headers
