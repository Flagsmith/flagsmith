import logging

import sentry_sdk
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class ForceSentryTraceMiddleware:
    """
    Middleware class to allow us to force Sentry traces on given requests.

    To use the middleware the application must be running in an environment with the
    FORCE_SENTRY_TRACE_AUTH_KEY environment variable set. Assuming that is done,
    simply add the `force_sentry_trace` query parameter to the request and ensure that
    the `X-Force-Sentry-Trace-Auth` header is set to the same value as the
    FORCE_SENTRY_TRACE_AUTH_KEY environment variable.
    """

    FORCE_SENTRY_TRACE_PARAM = "force_sentry_trace"
    FORCE_SENTRY_TRACE_HEADER = "X-Force-Sentry-Trace-Auth"

    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_key = settings.FORCE_SENTRY_TRACE_AUTH_KEY
        if not self.auth_key:
            logger.warning(
                "ForceSentryTraceMiddleware initialised without an auth key."
            )

    def __call__(self, request):
        if self.FORCE_SENTRY_TRACE_PARAM in request.GET:
            auth = request.headers.get(self.FORCE_SENTRY_TRACE_HEADER)
            if not auth or auth != self.auth_key:
                raise AuthenticationFailed(
                    "Incorrect authentication provided for forcing sentry trace."
                )

            sentry_sdk.start_transaction(
                name=f"{request.method} {request.path}", sampled=True
            )

        return self.get_response(request)
