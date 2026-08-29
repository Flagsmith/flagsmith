import sys

import pytest
from django.test import RequestFactory
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from app_analytics.middleware import APIUsageMiddleware
from app_analytics.models import Resource
from tests.types import EnableFeaturesFixture


@pytest.fixture(autouse=True)
def edge_proxy_not_installed(settings: SettingsWrapper) -> None:
    # Keep these tests hermetic: whether the private edge_proxy wheel is
    # installed in the test environment must not change middleware wiring.
    settings.EDGE_PROXY_INSTALLED = False


@pytest.mark.parametrize(
    "path, resource_name",
    [
        ("/api/v1/flags", "flags"),
        ("/api/v1/traits", "traits"),
        ("/api/v1/identities", "identities"),
        ("/api/v1/environment-document", "environment-document"),
    ],
)
def test_api_usage_middleware__cache_enabled__tracks_request_via_cache(
    rf: RequestFactory,
    mocker: MockerFixture,
    path: str,
    resource_name: str,
    settings: SettingsWrapper,
) -> None:
    # Given
    environment_key = "test"
    headers = {"HTTP_X-Environment-Key": environment_key}
    request = rf.get(path, **headers)  # type: ignore[arg-type]
    settings.USE_CACHE_FOR_USAGE_DATA = True

    mocked_api_usage_cache = mocker.patch(
        "app_analytics.services.api_usage_cache", autospec=True
    )

    mocked_get_response = mocker.MagicMock()
    middleware = APIUsageMiddleware(mocked_get_response)

    # When
    middleware(request)

    # Then
    mocked_api_usage_cache.track_request.assert_called_once_with(
        resource=Resource.get_from_name(resource_name),
        host="testserver",
        environment_key=environment_key,
        labels={},
    )


@pytest.mark.parametrize(
    "optional_headers,expected_labels",
    [
        ({}, {}),
        (
            {
                "HTTP_Flagsmith-Application-Name": "web",
                "HTTP_Flagsmith-Application-Version": "1.0",
                "HTTP_Unrelated-Header": "value",
            },
            {
                "client_application_name": "web",
                "client_application_version": "1.0",
            },
        ),
    ],
)
@pytest.mark.parametrize(
    "path, resource_name",
    [
        ("/api/v1/flags", "flags"),
        ("/api/v1/traits", "traits"),
        ("/api/v1/identities", "identities"),
        ("/api/v1/environment-document", "environment-document"),
    ],
)
def test_api_usage_middleware__no_cache__calls_expected(
    rf: RequestFactory,
    mocker: MockerFixture,
    enable_features: EnableFeaturesFixture,
    path: str,
    resource_name: str,
    settings: SettingsWrapper,
    optional_headers: dict[str, str],
    expected_labels: dict[str, str],
) -> None:
    # Given
    enable_features("sdk_metrics_labels")
    environment_key = "test"
    headers = {"HTTP_X-Environment-Key": environment_key, **optional_headers}
    request = rf.get(path, **headers)  # type: ignore[arg-type]
    settings.USE_CACHE_FOR_USAGE_DATA = False

    mocked_track_request = mocker.patch("app_analytics.services.track_request")

    mocked_get_response = mocker.MagicMock()
    middleware = APIUsageMiddleware(mocked_get_response)

    # When
    middleware(request)

    # Then
    mocked_track_request.run_in_thread.assert_called_once_with(
        kwargs={
            "resource": Resource.get_from_name(resource_name),
            "environment_key": environment_key,
            "host": "testserver",
            "labels": expected_labels,
        }
    )


def test_api_usage_middleware__request_not_tracked__not_calls_expected(
    rf: RequestFactory, mocker: MockerFixture, settings: SettingsWrapper
) -> None:
    # Given
    environment_key = "test"
    headers = {"HTTP_X-Environment-Key": environment_key}
    path = "/api/v1/unknown"
    request = rf.get(path, **headers)  # type: ignore[arg-type]
    settings.USE_CACHE_FOR_USAGE_DATA = False

    mocked_track_request = mocker.patch("app_analytics.services.track_request")

    mocked_get_response = mocker.MagicMock()
    middleware = APIUsageMiddleware(mocked_get_response)

    # When
    middleware(request)

    # Then
    mocked_track_request.delay.assert_not_called()


@pytest.mark.parametrize(
    "edge_proxy_installed, saas, expect_wired",
    [
        (True, False, True),
        (True, True, False),
        (False, False, False),
    ],
)
def test_api_usage_middleware__edge_proxy_check__wired_only_where_expected(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    edge_proxy_installed: bool,
    saas: bool,
    expect_wired: bool,
) -> None:
    # Given a deployment with/without the private edge_proxy app
    settings.EDGE_PROXY_INSTALLED = edge_proxy_installed
    mocker.patch("app_analytics.middleware.is_saas", return_value=saas)
    is_edge_proxy_request = mocker.MagicMock()
    mocker.patch.dict(
        sys.modules,
        {
            "edge_proxy": mocker.MagicMock(),
            "edge_proxy.authentication": mocker.MagicMock(
                is_edge_proxy_request=is_edge_proxy_request
            ),
        },
    )

    # When
    middleware = APIUsageMiddleware(mocker.MagicMock())

    # Then the verifier is wired only where the proxy reports usage
    # itself: a non-SaaS deployment with the edge_proxy app installed
    assert middleware.is_edge_proxy_request is (
        is_edge_proxy_request if expect_wired else None
    )


@pytest.mark.parametrize("is_verified_proxy_request", [True, False])
def test_api_usage_middleware__edge_proxy_check_wired__tracks_unverified_only(
    rf: RequestFactory,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    is_verified_proxy_request: bool,
) -> None:
    # Given a request bearing proxy headers the edge_proxy app does or
    # does not verify
    headers = {"HTTP_X-Environment-Key": "test", "HTTP_X-Proxy-Key": "pk.key"}
    request = rf.get("/api/v1/environment-document", **headers)  # type: ignore[arg-type]
    settings.EDGE_PROXY_INSTALLED = False
    mocked_track_usage = mocker.patch(
        "app_analytics.middleware.track_usage_by_resource_host_and_environment"
    )
    middleware = APIUsageMiddleware(mocker.MagicMock())
    middleware.is_edge_proxy_request = mocker.MagicMock(
        return_value=is_verified_proxy_request
    )

    # When
    middleware(request)

    # Then only a verified proxy request is exempt — a spoofed header is not
    middleware.is_edge_proxy_request.assert_called_once_with(request)
    assert mocked_track_usage.called is not is_verified_proxy_request


def test_api_usage_middleware__edge_proxy_check_not_wired__proxy_header_still_tracked(
    rf: RequestFactory,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given a request bearing an X-Proxy-Key on a deployment with no
    # edge_proxy app to verify it
    headers = {"HTTP_X-Environment-Key": "test", "HTTP_X-Proxy-Key": "pk.key"}
    request = rf.get("/api/v1/environment-document", **headers)  # type: ignore[arg-type]
    settings.EDGE_PROXY_INSTALLED = False
    mocked_track_usage = mocker.patch(
        "app_analytics.middleware.track_usage_by_resource_host_and_environment"
    )

    # When
    middleware = APIUsageMiddleware(mocker.MagicMock())
    middleware(request)

    # Then
    mocked_track_usage.assert_called_once()
