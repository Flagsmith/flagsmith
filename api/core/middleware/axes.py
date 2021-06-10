from axes.middleware import AxesMiddleware as DefaultAxesMiddleware
from django.conf import settings


class AxesMiddleware(DefaultAxesMiddleware):
    def __call__(self, request):
        if hasattr(request, "path") and any(
            url in request.path for url in settings.AXES_BLACKLISTED_URLS
        ):
            return super().__call__(request)

        response = self.get_response(request)
        return response
