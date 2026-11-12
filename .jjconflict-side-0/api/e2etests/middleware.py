from django.conf import settings


class E2ETestMiddleware:
    def __init__(self, get_response):  # type: ignore[no-untyped-def]
        self.get_response = get_response

    def __call__(self, request):  # type: ignore[no-untyped-def]
        request.is_e2e = False
        if (
            request.META.get("HTTP_X_E2E_TEST_AUTH_TOKEN")
            == settings.E2E_TEST_AUTH_TOKEN
        ):
            request.is_e2e = True

        return self.get_response(request)
