import pytest
from django.test import override_settings

from integrations.sentry.samplers import traces_sampler

SAMPLE_RATE = 0.5


@override_settings(DEFAULT_SENTRY_TRACE_SAMPLE_RATE=SAMPLE_RATE)
def test_traces_sampler_empty_context_returns_default_sample_rate():
    # When
    sample_rate = traces_sampler({})

    # Then
    assert sample_rate == SAMPLE_RATE


@override_settings(DEFAULT_SENTRY_TRACE_SAMPLE_RATE=SAMPLE_RATE)
def test_traces_sampler_returns_0_for_health_check_transaction():
    # Given
    ctx = {"wsgi_environ": {"PATH_INFO": "/health"}}

    # When
    sample_rate = traces_sampler(ctx)

    # Then
    assert sample_rate == 0


@override_settings(DEFAULT_SENTRY_TRACE_SAMPLE_RATE=SAMPLE_RATE)
def test_traces_sampler_returns_0_for_home_page_transaction():
    # Given
    ctx = {"wsgi_environ": {"PATH_INFO": "/"}}

    # When
    sample_rate = traces_sampler(ctx)

    # Then
    assert sample_rate == 0


@override_settings(DASHBOARD_ENDPOINTS_SENTRY_TRACE_SAMPLE_RATE=SAMPLE_RATE)
def test_traces_sampler_returns_dashboard_sample_rate_for_dashboard_request():
    # Given
    ctx = {"wsgi_environ": {"PATH_INFO": "/api/v1/environments/"}}

    # When
    sample_rate = traces_sampler(ctx)

    # Then
    assert sample_rate == SAMPLE_RATE


@pytest.mark.parametrize(
    "path_info",
    (
        "/api/v1/identities",
        "/api/v1/identities/",
        "/api/v1/flags",
        "/api/v1/traits",
        "/api/v1/environment-document",
        "/api/v1/traits/bulk",
    ),
)
@override_settings(DEFAULT_SENTRY_TRACE_SAMPLE_RATE=SAMPLE_RATE)
def test_traces_sampler_returns_sample_rate_for_sdk_request(path_info):
    # Given
    ctx = {"wsgi_environ": {"PATH_INFO": path_info}}

    # When
    sample_rate = traces_sampler(ctx)

    # Then
    assert sample_rate == SAMPLE_RATE
