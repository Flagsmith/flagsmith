import pytest
from rest_framework.exceptions import AuthenticationFailed

from integrations.sentry.middleware import ForceSentryTraceMiddleware


def test_force_sentry_trace_middleware_starts_transaction_when_param_present(
    rf, mocker, settings
):
    # Given
    mock_sentry_sdk = mocker.patch("integrations.sentry.middleware.sentry_sdk")

    auth_key = "auth-key"
    settings.FORCE_SENTRY_TRACE_AUTH_KEY = auth_key

    mock_response = mocker.MagicMock()
    middleware = ForceSentryTraceMiddleware(get_response=lambda r: mock_response)

    request = rf.get(
        path="/some-endpoint",
        data={ForceSentryTraceMiddleware.FORCE_SENTRY_TRACE_PARAM: "1"},
        HTTP_X_FORCE_SENTRY_TRACE_AUTH=auth_key,
    )

    # When
    response = middleware(request)

    # Then
    mock_sentry_sdk.start_transaction.assert_called_once_with(
        name="GET /some-endpoint", sampled=True
    )
    assert response == mock_response


def test_force_sentry_trace_middleware_raises_exception_when_auth_incorrect(
    rf, mocker, settings
):
    # Given
    mock_sentry_sdk = mocker.patch("integrations.sentry.middleware.sentry_sdk")

    settings.FORCE_SENTRY_TRACE_AUTH_KEY = "auth-key"

    mock_response = mocker.MagicMock()
    middleware = ForceSentryTraceMiddleware(get_response=lambda r: mock_response)

    request = rf.get(
        path="/some-endpoint",
        data={ForceSentryTraceMiddleware.FORCE_SENTRY_TRACE_PARAM: "1"},
        HTTP_X_FORCE_SENTRY_TRACE_AUTH="some-incorrect-auth",
    )

    # When
    with pytest.raises(AuthenticationFailed):
        middleware(request)

    # Then
    mock_sentry_sdk.start_transaction.assert_not_called()
