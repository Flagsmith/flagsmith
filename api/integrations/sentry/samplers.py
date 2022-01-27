from django.conf import settings


def block_non_functional_endpoints_sampler(ctx):
    non_functional_endpoints = ["/health", "/"]

    sample_rate = settings.SENTRY_TRACE_SAMPLE_RATE
    wsgi_env = ctx.get("wsgi_environ")
    if wsgi_env and wsgi_env.get("PATH_INFO") in non_functional_endpoints:
        sample_rate = 0
    return sample_rate
