from datetime import timedelta

import pytest
from django.utils import timezone
from task_processor.task_run_method import TaskRunMethod

from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.subscription_info_cache import update_caches
from organisations.subscriptions.constants import SubscriptionCacheEntity


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_update_caches(mocker, organisation, chargebee_subscription, settings):
    # Given
    settings.CHARGEBEE_API_KEY = "api-key"
    settings.INFLUXDB_TOKEN = "token"
    settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY

    now = timezone.now()
    day_1 = now - timedelta(days=1)
    day_7 = now - timedelta(days=7)
    day_30 = now - timedelta(days=30)
    organisation_usage = {
        day_1: 25123,
        day_7: 182957,
        day_30: 804564,
    }
    mocked_get_top_organisations = mocker.patch(
        "organisations.subscription_info_cache.get_top_organisations"
    )
    mocked_get_top_organisations.side_effect = lambda t, _: {
        organisation.id: organisation_usage[t]
    }

    chargebee_metadata = ChargebeeObjMetadata(seats=15, api_calls=1000000)
    mocked_get_subscription_metadata = mocker.patch(
        "organisations.subscription_info_cache.get_subscription_metadata_from_id"
    )
    mocked_get_subscription_metadata.return_value = chargebee_metadata

    # When
    subscription_cache_entities = (
        SubscriptionCacheEntity.INFLUX,
        SubscriptionCacheEntity.CHARGEBEE,
    )
    update_caches(subscription_cache_entities)

    # Then
    assert (
        organisation.subscription_information_cache.api_calls_24h
        == organisation_usage[day_1]
    )
    assert (
        organisation.subscription_information_cache.api_calls_7d
        == organisation_usage[day_7]
    )
    assert (
        organisation.subscription_information_cache.api_calls_30d
        == organisation_usage[day_30]
    )
    assert (
        organisation.subscription_information_cache.allowed_seats
        == chargebee_metadata.seats
    )
    assert (
        organisation.subscription_information_cache.allowed_30d_api_calls
        == chargebee_metadata.api_calls
    )

    mocked_get_subscription_metadata.assert_called_once_with(
        chargebee_subscription.subscription_id
    )

    assert mocked_get_top_organisations.call_count == 3
    assert [call[0] for call in mocked_get_top_organisations.call_args_list] == [
        (day_30, ""),
        (day_7, ""),
        (day_1, "100"),
    ]
