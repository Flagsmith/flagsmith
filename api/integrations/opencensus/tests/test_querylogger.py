from unittest.mock import create_autospec

from integrations.opencensus.querylogger import QueryLogger


def test_querylogger_when_tracer_not_set_then_query_is_executed(mocker):
    # Given
    execution_context = mocker.patch(
        "integrations.opencensus.querylogger.execution_context"
    )
    execution_context.get_opencensus_tracer.return_value = None

    execute = create_autospec(lambda s, p, m, c: None)
    sql = "select * from table"
    params = [3, 2, 1]
    context = mocker.MagicMock()

    logger = QueryLogger()

    # When
    logger(execute, sql=sql, params=params, many="", context=context)

    # Then
    execute.assert_called_once_with(sql, params, "", context)


def test_querylogger_when_query_is_executed_then_new_span_is_created(mocker):
    # Given
    span = mocker.MagicMock()
    tracer = mocker.MagicMock()
    tracer.start_span.return_value = span

    execution_context = mocker.patch(
        "integrations.opencensus.querylogger.execution_context"
    )
    execution_context.get_opencensus_tracer.return_value = tracer

    context = mocker.MagicMock()
    mock_response = mocker.MagicMock()

    execute = create_autospec(lambda s, p, m, c: mock_response)

    sql = "select * from table"
    params = [3, 2, 1]

    logger = QueryLogger()

    # When
    logger(execute, sql=sql, params=params, many="", context=context)

    # Then
    execute.assert_called_once_with(sql, params, "", context)
    tracer.start_span.assert_called_once()
    tracer.add_attribute_to_current_span.assert_called()
    tracer.end_span.assert_called_once()


def test_querylogger_when_query_execution_fails_then_span_is_created(mocker):
    # Given
    span = mocker.MagicMock()
    tracer = mocker.MagicMock()
    tracer.start_span.return_value = span

    execution_context = mocker.patch(
        "integrations.opencensus.querylogger.execution_context"
    )
    execution_context.get_opencensus_tracer.return_value = tracer

    context = mocker.MagicMock()

    execute = mocker.Mock()
    execute.side_effect = Exception("Boom!")

    sql = "select * from table"
    params = [3, 2, 1]

    logger = QueryLogger()

    # When
    try:
        logger(execute, sql=sql, params=params, many="", context=context)
    except Exception:
        pass

    # Then
    execute.assert_called_once_with(sql, params, "", context)
    tracer.start_span.assert_called_once()
    tracer.add_attribute_to_current_span.assert_called()
    tracer.end_span.assert_called_once()
