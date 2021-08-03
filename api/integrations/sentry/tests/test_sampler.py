from django.conf import settings

from integrations.sentry.samplers import block_health_sampler


def test_block_health_sampler_empty_context_returns_defaut_sample_rate():
    # Given
    settings.SENTRY_TRACE_SAMPLE_RATE = 10

    # When
    sample_rate = block_health_sampler({})

    # Then
    assert sample_rate == 10


def test_block_health_sampler_returns_0_for_health_check_transaction():
    # Given
    settings.SENTRY_TRACE_SAMPLE_RATE = 10
    ctx = {"wsgi_environ": {"PATH_INFO": "/health"}}

    # When
    sample_rate = block_health_sampler(ctx)

    # Then
    assert sample_rate == 0


def test_block_health_sampler_returns_default_for_non_heath_check_transaction():
    # Given
    settings.SENTRY_TRACE_SAMPLE_RATE = 10
    ctx = {"wsgi_env": {"PATH_INFO": "/home"}}

    # When
    sample_rate = block_health_sampler(ctx)

    # Then
    assert sample_rate == 10
