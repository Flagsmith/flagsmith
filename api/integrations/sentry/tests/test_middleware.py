from integrations.sentry.middleware import ForceSentryTraceMiddleware


def test_force_sentry_trace_middleware_starts_transaction_when_param_present(
    rf, mocker, settings
):
    # Given
    mock_sentry_sdk = mocker.patch("integrations.sentry.middleware.sentry_sdk")
    mock_start_transaction_context_manager = mocker.MagicMock()
    mock_sentry_sdk.start_transaction.return_value = (
        mock_start_transaction_context_manager
    )

    auth_key = "auth-key"
    settings.FORCE_SENTRY_TRACE_KEY = auth_key

    mock_response = mocker.MagicMock()
    middleware = ForceSentryTraceMiddleware(get_response=lambda r: mock_response)

    request = rf.get(path="/some-endpoint", HTTP_X_FORCE_SENTRY_TRACE_KEY=auth_key)

    # When
    response = middleware(request)

    # Then
    mock_sentry_sdk.start_transaction.assert_called_once_with(
        name="GET /some-endpoint", sampled=True
    )
    mock_start_transaction_context_manager.__enter__.assert_called_once()
    assert response == mock_response


def test_force_sentry_trace_middleware_does_nothing_when_key_incorrect(
    rf, mocker, settings
):
    # Given
    mock_sentry_sdk = mocker.patch("integrations.sentry.middleware.sentry_sdk")

    settings.FORCE_SENTRY_TRACE_KEY = "auth-key"

    mock_response = mocker.MagicMock()
    middleware = ForceSentryTraceMiddleware(get_response=lambda r: mock_response)

    request = rf.get(
        path="/some-endpoint", HTTP_X_FORCE_SENTRY_TRACE_KEY="some-incorrect-auth"
    )

    # When
    response = middleware(request)

    # Then
    mock_sentry_sdk.start_transaction.assert_not_called()
    assert response == mock_response


def test_force_sentry_trace_middleware_does_nothing_when_key_missing(
    rf, mocker, settings
):
    # Given
    mock_sentry_sdk = mocker.patch("integrations.sentry.middleware.sentry_sdk")

    settings.FORCE_SENTRY_TRACE_KEY = "auth-key"

    mock_response = mocker.MagicMock()
    middleware = ForceSentryTraceMiddleware(get_response=lambda r: mock_response)

    request = rf.get(path="/some-endpoint")

    # When
    response = middleware(request)

    # Then
    mock_sentry_sdk.start_transaction.assert_not_called()
    assert response == mock_response
