from django.http import HttpRequest, HttpResponse

from metrics.worker_metrics import update_worker_metrics


class WorkerRSSMiddleware:
    def __init__(self, get_response):  # type: ignore[no-untyped-def]
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        try:
            update_worker_metrics()
        except Exception:
            pass
        return response
