import os

from common.core.otel import add_otel_trace_context
from opentelemetry import baggage
from opentelemetry import context as otel_context
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
    [span_processor] = (
        build_tracer_provider_mock.return_value.add_span_processor.call_args.args
    )
    assert isinstance(span_processor, telemetry.FlagsmithBaggageSpanProcessor)
    setup_logging_mock.assert_called_once_with(
        log_level="DEBUG",
        log_format="json",
        application_loggers=telemetry.APPLICATION_LOGGERS,
        otel_processors=[
            add_otel_trace_context,
            make_structlog_otel_processor_mock.return_value,
        ],
    )


async def test_baggage_middleware__uninitialised_session__tool_name_baggage_only(
    mocker: MockerFixture,
) -> None:
    # Given a tool call outside an initialised session
    middleware = telemetry.BaggageMiddleware()
    context = mocker.Mock()
    context.message.name = "list_environments"
    seen_baggage: dict[str, object] = {}

    async def record_baggage(ctx: object) -> None:
        seen_baggage.update(baggage.get_all())

    call_next = mocker.AsyncMock(side_effect=record_baggage)

    # When
    await middleware.on_call_tool(context, call_next)

    # Then
    assert seen_baggage == {"flagsmith.tool.name": "list_environments"}
    assert baggage.get_all() == {}


async def test_baggage_middleware__uninitialised_session__request_baggage_untouched(
    mocker: MockerFixture,
) -> None:
    # Given a request outside an initialised session
    middleware = telemetry.BaggageMiddleware()
    seen_baggage: dict[str, object] = {}

    async def record_baggage(ctx: object) -> None:
        seen_baggage.update(baggage.get_all())

    call_next = mocker.AsyncMock(side_effect=record_baggage)

    # When
    await middleware.on_request(mocker.Mock(), call_next)

    # Then
    assert seen_baggage == {}


def test_flagsmith_baggage_span_processor__foreign_baggage__not_copied(
    mocker: MockerFixture,
) -> None:
    # Given baggage with flagsmith and foreign entries
    span = mocker.Mock()
    ctx = baggage.set_baggage("other.key", "x")
    ctx = baggage.set_baggage("flagsmith.tool.name", "list_environments", context=ctx)
    token = otel_context.attach(ctx)

    # When
    try:
        telemetry.FlagsmithBaggageSpanProcessor().on_start(span)
    finally:
        otel_context.detach(token)

    # Then
    span.set_attribute.assert_called_once_with(
        "flagsmith.tool.name", "list_environments"
    )
