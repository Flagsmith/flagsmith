from django.db import connection

from .querylogger import QueryLogger


class OpenCensusDbTraceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ql = QueryLogger()
        with connection.execute_wrapper(ql):
            response = self.get_response(request)

        return response
