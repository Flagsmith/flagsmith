import os

from django.conf import settings as django_settings
from django.test import Client, override_settings
from prometheus_client import REGISTRY, generate_latest
from pytest_mock import MockerFixture

from metrics.worker_metrics import clear_worker_metrics


@override_settings(
    MIDDLEWARE=[
        *django_settings.MIDDLEWARE,
        "core.middleware.worker_rss.WorkerRSSMiddleware",
    ]
)
def test_worker_rss_metric__request_through_middleware__appears_in_prometheus_output(
    client: Client,
    mocker: MockerFixture,
) -> None:
    # Given - deterministic RSS reading so the test is independent of /proc availability
    # on macOS/Windows CI runners.
    expected_rss = 12_345_678
    mocker.patch(
        "metrics.worker_metrics.get_current_process_max_rss_bytes",
        return_value=expected_rss,
    )

    # When - any cheap, known-reachable endpoint trips the middleware after response.
    response = client.get("/api/v1/swagger.json", HTTP_ACCEPT="application/json")

    # Then - the response is unaffected by the middleware, and the gauge is exposed
    # with a sample for the current worker's PID via the Prometheus exposition format.
    assert response.status_code == 200
    output = generate_latest(REGISTRY).decode()
    assert "flagsmith_worker_rss_bytes" in output
    assert f'pid="{os.getpid()}"' in output


def teardown_function(function: object) -> None:
    # Prevent labelled-child leakage to other tests in the same xdist worker by removing
    # this PID's sample after each test. Uses the existing module API.
    try:
        clear_worker_metrics()
    except Exception:
        pass
