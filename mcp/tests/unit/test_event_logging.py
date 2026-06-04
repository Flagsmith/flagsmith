from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from flagsmith_mcp import events


def test_get_client_info__outside_request_context__returns_none() -> None:
    # Given no MCP request context
    # When / Then
    assert events.get_client_info() is None


def test_get_client_info__no_client_params__returns_none(
    mocker: MockerFixture,
) -> None:
    # Given a session that has not yet completed initialize
    context_mock = mocker.patch.object(events, "get_context", autospec=True)
    context_mock.return_value.session.client_params = None

    # When / Then
    assert events.get_client_info() is None


async def test_event_logging_middleware__no_client_info__empty_client_identity(
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    middleware = events.EventLoggingMiddleware()
    context = mocker.Mock()
    context.message.name = "list_environments"
    call_next = mocker.AsyncMock()

    # When
    await middleware.on_call_tool(context, call_next)

    # Then
    assert log.has(
        "tool.called",
        tool__name="list_environments",
        flagsmith__client__name="",
        flagsmith__client__version="",
        status="success",
    )
