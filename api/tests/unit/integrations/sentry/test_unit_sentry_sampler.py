import pytest
from django.test import override_settings

from integrations.sentry.samplers import traces_sampler

SAMPLE_RATE = 0.5


@override_settings(DEFAULT_SENTRY_TRACE_SAMPLE_RATE=SAMPLE_RATE)
def test_traces_sampler__empty_context__returns_default_sample_rate():  # type: ignore[no-untyped-def]
    # Given
    ctx: dict[str, object] = {}

    # When
    sample_rate = traces_sampler(ctx)  # type: ignore[no-untyped-call]

    # Then
    assert sample_rate == SAMPLE_RATE


@override_settings(DEFAULT_SENTRY_TRACE_SAMPLE_RATE=SAMPLE_RATE)
def test_traces_sampler__health_check_path__returns_zero():  # type: ignore[no-untyped-def]
    # Given
    ctx = {"wsgi_environ": {"PATH_INFO": "/health"}}

    # When
    sample_rate = traces_sampler(ctx)  # type: ignore[no-untyped-call]

    # Then
    assert sample_rate == 0


@override_settings(DEFAULT_SENTRY_TRACE_SAMPLE_RATE=SAMPLE_RATE)
def test_traces_sampler__home_page_path__returns_zero():  # type: ignore[no-untyped-def]
    # Given
    ctx = {"wsgi_environ": {"PATH_INFO": "/"}}

    # When
    sample_rate = traces_sampler(ctx)  # type: ignore[no-untyped-call]

    # Then
    assert sample_rate == 0


@override_settings(DASHBOARD_ENDPOINTS_SENTRY_TRACE_SAMPLE_RATE=SAMPLE_RATE)
def test_traces_sampler__dashboard_request__returns_dashboard_sample_rate():  # type: ignore[no-untyped-def]
    # Given
    ctx = {"wsgi_environ": {"PATH_INFO": "/api/v1/environments/"}}

    # When
    sample_rate = traces_sampler(ctx)  # type: ignore[no-untyped-call]

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
def test_traces_sampler__sdk_request_path__returns_default_sample_rate(path_info):  # type: ignore[no-untyped-def]
    # Given
    ctx = {"wsgi_environ": {"PATH_INFO": path_info}}

    # When
    sample_rate = traces_sampler(ctx)  # type: ignore[no-untyped-call]

    # Then
    assert sample_rate == SAMPLE_RATE
