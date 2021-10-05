from .track import (
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
