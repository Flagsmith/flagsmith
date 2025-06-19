from typing import Callable

from django.http import HttpRequest, HttpResponse

from app_analytics.mappers import map_request_to_labels
from app_analytics.services import track_usage_by_resource_host_and_environment

from .track import (
    get_resource_from_uri,
    track_request_googleanalytics_async,
)


class GoogleAnalyticsMiddleware:
    def __init__(self, get_response):  # type: ignore[no-untyped-def]
        self.get_response = get_response

    def __call__(self, request):  # type: ignore[no-untyped-def]
        # for each API request, trigger a call to Google Analytics to track the request
        track_request_googleanalytics_async(request)

        response = self.get_response(request)

        return response


class APIUsageMiddleware:
    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if environment_key := request.headers.get("X-Environment-Key"):
            track_usage_by_resource_host_and_environment(
                resource=get_resource_from_uri(request.path),
                host=request.get_host(),
                environment_key=environment_key,
                labels=map_request_to_labels(request),
            )

        response = self.get_response(request)

        return response
