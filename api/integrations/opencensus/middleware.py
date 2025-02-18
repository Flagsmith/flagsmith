from django.db import connection

from .querylogger import QueryLogger


class OpenCensusDbTraceMiddleware:
    def __init__(self, get_response):  # type: ignore[no-untyped-def]
        self.get_response = get_response

    def __call__(self, request):  # type: ignore[no-untyped-def]
        ql = QueryLogger()  # type: ignore[no-untyped-call]
        with connection.execute_wrapper(ql):
            response = self.get_response(request)

        return response
