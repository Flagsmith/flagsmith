from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.models import OrganisationSubscriptionInformationCache
from task_processor.task_run_method import TaskRunMethod


def test_organisation_subscription_information_cache_update_caches(
    mocker, organisation, chargebee_subscription, settings
):
    # Given
    settings.CHARGEBEE_API_KEY = "api-key"
    settings.INFLUXDB_TOKEN = "token"
    settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY

    organisation_usage = {"24h": 25123, "7d": 182957, "30d": 804564}
    mocked_get_top_organisations = mocker.patch(
        "organisations.models.get_top_organisations"
    )
    mocked_get_top_organisations.side_effect = lambda t, _: {
        organisation.id: organisation_usage.get(t)
    }

    chargebee_metadata = ChargebeeObjMetadata(seats=15, api_calls=1000000)
    mocked_get_subscription_metadata = mocker.patch(
        "organisations.models.get_subscription_metadata"
    )
    mocked_get_subscription_metadata.return_value = chargebee_metadata

    # When
    OrganisationSubscriptionInformationCache.update_caches()

    # Then
    assert organisation.subscription_information_cache.updated_at
    assert (
        organisation.subscription_information_cache.api_calls_24h
        == organisation_usage["24h"]
    )
    assert (
        organisation.subscription_information_cache.api_calls_7d
        == organisation_usage["7d"]
    )
    assert (
        organisation.subscription_information_cache.api_calls_30d
        == organisation_usage["30d"]
    )
    assert (
        organisation.subscription_information_cache.allowed_seats
        == chargebee_metadata.seats
    )
    assert (
        organisation.subscription_information_cache.allowed_30d_api_calls
        == chargebee_metadata.api_calls
    )
