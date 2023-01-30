from .models import Resource
from .tasks import track_request
from .track import (
    TRACKED_RESOURCE_ACTIONS,
    get_resource_from_uri,
    track_request_googleanalytics_async,
    track_request_influxdb_async,
)


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
            track_request.delay(
                kwargs={
                    "resource": Resource.get_from_resource_name(resource),
                    "host": request.get_host(),
                    "environment_key": request.headers.get("X-Environment-Key"),
                }
            )

        response = self.get_response(request)

        return response
