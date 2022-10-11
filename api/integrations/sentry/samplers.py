import re

from django.conf import settings

NON_FUNCTIONAL_ENDPOINTS = {"/health", "/"}
sdk_endpoint_matcher = re.compile(
    r"/api/v1/(traits|identities|flags|environment-document)/*.*"
)


def traces_sampler(ctx):
    wsgi_env = ctx.get("wsgi_environ")

    if wsgi_env:
        path_info = wsgi_env.get("PATH_INFO", "")

        if path_info in NON_FUNCTIONAL_ENDPOINTS:
            return 0
        elif not sdk_endpoint_matcher.match(path_info):
            # request must be a call to the 'dashboard' API. Note: we check prefixes, so we can ignore any redirected
            # requests for trailing slash appending.
            return 1

    return settings.SENTRY_TRACE_SAMPLE_RATE
