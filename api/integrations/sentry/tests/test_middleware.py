from integrations.sentry.middleware import ForceSentryTraceMiddleware


def test_force_sentry_trace_middleware_starts_transaction_when_param_present(
    rf, mocker
):
    # Given
    mock_sentry_sdk = mocker.patch("integrations.sentry.middleware.sentry_sdk")

    mock_response = mocker.MagicMock()
    middleware = ForceSentryTraceMiddleware(get_response=lambda r: mock_response)
    request = rf.get(
        path="/some-endpoint",
        data={ForceSentryTraceMiddleware.FORCE_SENTRY_TRACE_PARAM: "1"},
    )

    # When
    response = middleware(request)

    # Then
    mock_sentry_sdk.start_transaction.assert_called_once_with(
        name="GET /some-endpoint", sampled=True
    )
    assert response == mock_response
