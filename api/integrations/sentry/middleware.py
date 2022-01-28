import logging

import sentry_sdk
from django.conf import settings

logger = logging.getLogger(__name__)


class ForceSentryTraceMiddleware:
    """
    Middleware class to allow us to force Sentry traces on given requests.

    To use the middleware the application must be running in an environment with the
    FORCE_SENTRY_TRACE_KEY environment variable set. Assuming that is done,
    simply add the `X-Force-Sentry-Trace-Key` header to any request and make sure it
    is set to the same value as the FORCE_SENTRY_TRACE_AUTH_KEY environment variable.
    """

    FORCE_SENTRY_TRACE_HEADER = "X-Force-Sentry-Trace-Key"

    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_key = settings.FORCE_SENTRY_TRACE_KEY

    def __call__(self, request):
        auth = request.headers.get(self.FORCE_SENTRY_TRACE_HEADER)
        if auth == self.auth_key:
            sentry_sdk.start_transaction(
                name=f"{request.method} {request.path}", sampled=True
            )

        return self.get_response(request)
