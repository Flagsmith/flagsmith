from axes.middleware import (  # type: ignore[import-untyped]
    AxesMiddleware as DefaultAxesMiddleware,
)
from django.conf import settings


class AxesMiddleware(DefaultAxesMiddleware):  # type: ignore[misc]
    def __call__(self, request):  # type: ignore[no-untyped-def]
        if hasattr(request, "path") and any(
            url in request.path for url in settings.AXES_BLACKLISTED_URLS
        ):
            return super().__call__(request)

        response = self.get_response(request)
        return response
