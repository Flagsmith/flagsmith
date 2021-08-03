from django.conf import settings


def block_health_sampler(ctx):
    sample_rate = settings.SENTRY_TRACE_SAMPLE_RATE
    wsgi_env = ctx.get("wsgi_environ")
    if wsgi_env and wsgi_env.get("PATH_INFO") == "/health":
        sample_rate = 0
    return sample_rate
