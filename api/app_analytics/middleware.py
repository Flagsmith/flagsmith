from app_analytics.cache import APIUsageCache
from app_analytics.tasks import track_request
from django.conf import settings

from .models import Resource
from .track import (
    TRACKED_RESOURCE_ACTIONS,
    get_resource_from_uri,
    track_request_googleanalytics_async,
    track_request_influxdb_async,
)

api_usage_cache = APIUsageCache()


class GoogleAnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # for each API request, trigger a call to Google Analytics to track the request
        track_request_googleanalytics_async(request)

        response = self.get_response(request)

        return response


class InfluxDBMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # for each API request, trigger a call to InfluxDB to track the request
        track_request_influxdb_async(request)

        response = self.get_response(request)

        return response


class APIUsageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resource = get_resource_from_uri(request.path)
        if resource in TRACKED_RESOURCE_ACTIONS:
            kwargs = {
                "resource": Resource.get_from_resource_name(resource),
                "host": request.get_host(),
                "environment_key": request.headers.get("X-Environment-Key"),
            }
            if settings.USE_CACHE_FOR_USAGE_DATA:
                api_usage_cache.track_request(**kwargs)
            else:
                track_request.delay(kwargs=kwargs)

        response = self.get_response(request)

        return response
