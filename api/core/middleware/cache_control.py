from django.utils.cache import add_never_cache_headers


class NeverCacheMiddleware:
    def __init__(self, get_response):  # type: ignore[no-untyped-def]
        self.get_response = get_response

    def __call__(self, request):  # type: ignore[no-untyped-def]
        response = self.get_response(request)
        add_never_cache_headers(response)
        response["Pragma"] = "no-cache"
        return response
