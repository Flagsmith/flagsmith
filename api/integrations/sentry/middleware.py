import sentry_sdk


class ForceSentryTraceMiddleware:
    FORCE_SENTRY_TRACE_PARAM = "force_sentry_trace"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self.FORCE_SENTRY_TRACE_PARAM in request.GET:
            sentry_sdk.start_transaction(
                name=f"{request.method} {request.path}", sampled=True
            )

        return self.get_response(request)
