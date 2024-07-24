import pytest
from app_analytics.middleware import APIUsageMiddleware
from app_analytics.models import Resource
from django.test import RequestFactory
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture


@pytest.mark.parametrize(
    "path, enum_resource_value",
    [
        ("/api/v1/flags", Resource.FLAGS),
        ("/api/v1/traits", Resource.TRAITS),
        ("/api/v1/identities", Resource.IDENTITIES),
        ("/api/v1/environment-document", Resource.ENVIRONMENT_DOCUMENT),
    ],
)
def test_APIUsageMiddleware_calls_track_request_correctly_with_cache(
    rf: RequestFactory,
    mocker: MockerFixture,
    path: str,
    enum_resource_value: int,
    settings: SettingsWrapper,
) -> None:
    # Given
    environment_key = "test"
    headers = {"HTTP_X-Environment-Key": environment_key}
    request = rf.get(path, **headers)
    settings.USE_CACHE_FOR_USAGE_DATA = True

    mocked_api_usage_cache = mocker.patch(
        "app_analytics.middleware.api_usage_cache", autospec=True
    )

    mocked_get_response = mocker.MagicMock()
    middleware = APIUsageMiddleware(mocked_get_response)

    # When
    middleware(request)

    # Then
    mocked_api_usage_cache.track_request.assert_called_once_with(
        resource=enum_resource_value, host="testserver", environment_key=environment_key
    )


@pytest.mark.parametrize(
    "path, enum_resource_value",
    [
        ("/api/v1/flags", Resource.FLAGS),
        ("/api/v1/traits", Resource.TRAITS),
        ("/api/v1/identities", Resource.IDENTITIES),
        ("/api/v1/environment-document", Resource.ENVIRONMENT_DOCUMENT),
    ],
)
def test_APIUsageMiddleware_calls_track_request_correctly_without_cache(
    rf: RequestFactory,
    mocker: MockerFixture,
    path: str,
    enum_resource_value: int,
    settings: SettingsWrapper,
) -> None:
    # Given
    environment_key = "test"
    headers = {"HTTP_X-Environment-Key": environment_key}
    request = rf.get(path, **headers)
    settings.USE_CACHE_FOR_USAGE_DATA = False

    mocked_track_request = mocker.patch("app_analytics.middleware.track_request")

    mocked_get_response = mocker.MagicMock()
    middleware = APIUsageMiddleware(mocked_get_response)

    # When
    middleware(request)

    # Then
    mocked_track_request.delay.assert_called_once_with(
        kwargs={
            "resource": enum_resource_value,
            "environment_key": environment_key,
            "host": "testserver",
        }
    )


def test_APIUsageMiddleware_avoids_calling_track_request_if_resoure_is_not_tracked(
    rf: RequestFactory, mocker: MockerFixture, settings: SettingsWrapper
) -> None:
    # Given
    environment_key = "test"
    headers = {"HTTP_X-Environment-Key": environment_key}
    path = "/api/v1/unknown"
    request = rf.get(path, **headers)
    settings.USE_CACHE_FOR_USAGE_DATA = False

    mocked_track_request = mocker.patch("app_analytics.middleware.track_request")

    mocked_get_response = mocker.MagicMock()
    middleware = APIUsageMiddleware(mocked_get_response)

    # When
    middleware(request)

    # Then
    mocked_track_request.delay.assert_not_called()
