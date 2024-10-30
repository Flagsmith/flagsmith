from typing import Any

import pytest
from django.core.management import call_command
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture


def test_populate_buckets__postgres_analytics_disabled__noop(
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False
    populate_api_usage_bucket_mock = mocker.patch(
        "app_analytics.management.commands.populate_buckets.populate_api_usage_bucket"
    )
    populate_feature_evaluation_bucket = mocker.patch(
        "app_analytics.management.commands.populate_buckets.populate_feature_evaluation_bucket"
    )

    # When
    call_command("populate_buckets")

    # Then
    populate_api_usage_bucket_mock.assert_not_called()
    populate_feature_evaluation_bucket.assert_not_called()


@pytest.mark.parametrize(
    "options, expected_call_every",
    [
        ({}, 43200),
        (
            {"days_to_populate": 10},
            14400,
        ),
    ],
)
def test_populate_buckets__postgres_analytics_enabled__calls_expected(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    options: dict[str, Any],
    expected_call_every: int,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True
    populate_api_usage_bucket_mock = mocker.patch(
        "app_analytics.management.commands.populate_buckets.populate_api_usage_bucket"
    )
    populate_feature_evaluation_bucket = mocker.patch(
        "app_analytics.management.commands.populate_buckets.populate_feature_evaluation_bucket"
    )
    expected_bucket_size = 15
    mocker.patch(
        "app_analytics.management.commands.populate_buckets.ANALYTICS_READ_BUCKET_SIZE",
        new=expected_bucket_size,
    )

    # When
    call_command("populate_buckets", **options)

    # Then
    populate_api_usage_bucket_mock.assert_called_once_with(
        expected_bucket_size,
        expected_call_every,
    )
    populate_feature_evaluation_bucket.assert_called_once_with(
        expected_bucket_size,
        expected_call_every,
    )
