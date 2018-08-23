from .utils import track_request


class GoogleAnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # for each API request, trigger a call to Google Analytics to track the request
        if request.path:
            track_request(request.path)

        response = self.get_response(request)

        return response
