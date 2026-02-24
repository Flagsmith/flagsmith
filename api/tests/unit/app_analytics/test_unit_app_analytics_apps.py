from django.apps import apps
from pytest_mock import MockerFixture

from app_analytics.apps import flush_analytics_caches


def test_app_analytics_config__ready__registers_atexit_handler(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_atexit_register = mocker.patch("app_analytics.apps.atexit.register")
    config = apps.get_app_config("app_analytics")

    # When
    config.ready()

    # Then
    mock_atexit_register.assert_called_once_with(flush_analytics_caches)


def test_flush_analytics_caches__calls_flush_on_shutdown_on_both_caches(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_api_usage_cache = mocker.patch(
        "app_analytics.services.api_usage_cache",
    )
    mock_feature_evaluation_cache = mocker.patch(
        "app_analytics.views.feature_evaluation_cache",
    )

    # When
    flush_analytics_caches()

    # Then
    mock_api_usage_cache.flush_on_shutdown.assert_called_once()
    mock_feature_evaluation_cache.flush_on_shutdown.assert_called_once()


def test_flush_analytics_caches__exception__logs_and_does_not_raise(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_cache = mocker.patch("app_analytics.services.api_usage_cache")
    mock_cache.flush_on_shutdown.side_effect = RuntimeError("test error")
    mock_logger = mocker.patch("app_analytics.apps.logger")

    # When — should not raise
    flush_analytics_caches()

    # Then
    mock_logger.exception.assert_called_once_with(
        "Failed to flush analytics caches during shutdown"
    )
