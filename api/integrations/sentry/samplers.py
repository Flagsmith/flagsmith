from contextlib import suppress

from django.conf import settings

NON_FUNCTIONAL_ENDPOINTS = ("/health", "")
SDK_ENDPOINTS = {
    "/api/v1/flags",
    "/api/v1/identities",
    "/api/v1/traits",
    "/api/v1/traits/bulk",
    "/api/v1/environment-document",
    "/api/v1/analytics/flags",
    "/api/v2/analytics/flags",
}


def traces_sampler(ctx):
    with suppress(KeyError):
        path_info = ctx["wsgi_environ"]["PATH_INFO"]
        path_info = path_info[:-1] if path_info.endswith("/") else path_info

        if path_info in NON_FUNCTIONAL_ENDPOINTS:
            return 0
        elif path_info not in SDK_ENDPOINTS:
            return settings.DASHBOARD_ENDPOINTS_SENTRY_TRACE_SAMPLE_RATE

    return settings.DEFAULT_SENTRY_TRACE_SAMPLE_RATE
