from integrations.opencensus.middleware import OpenCensusDbTraceMiddleware


def test_open_census_db_trace_middleware_when_called_then_adds_execution_wrapper(
    rf, mocker
):
    # Given
    connection = mocker.patch("integrations.opencensus.middleware.connection")

    mock_response = mocker.MagicMock()
    sut = OpenCensusDbTraceMiddleware(get_response=lambda r: mock_response)
    request = rf.get(path="/some-endpoint")

    # When
    response = sut(request)

    # Then
    assert response == mock_response
    connection.execute_wrapper.assert_called_once()
