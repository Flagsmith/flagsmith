from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from app_analytics.cache import APIUsageCache
from app_analytics.tasks import track_request

from .track import (
    TRACKED_RESOURCE_ACTIONS,
    get_resource_from_uri,
    track_request_googleanalytics_async,
)

api_usage_cache = APIUsageCache()


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
        environment_key = request.headers.get("X-Environment-Key")
        if environment_key and (
            (resource := get_resource_from_uri(request.path))
            in TRACKED_RESOURCE_ACTIONS
        ):
            kwargs = {
                "resource": resource,
                "host": request.get_host(),
                "environment_key": environment_key,
            }
            if settings.USE_CACHE_FOR_USAGE_DATA:
                api_usage_cache.track_request(**kwargs)
            else:
                track_request.delay(kwargs=kwargs)

        response = self.get_response(request)

        return response
