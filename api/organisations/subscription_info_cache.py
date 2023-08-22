import typing

from app_analytics.influxdb_wrapper import get_top_organisations
from django.conf import settings

from .chargebee import get_subscription_metadata_from_id
from .models import Organisation, OrganisationSubscriptionInformationCache
from .subscriptions.constants import CHARGEBEE, SubscriptionCacheEntity

OrganisationSubscriptionInformationCacheDict = typing.Dict[
    int, OrganisationSubscriptionInformationCache
]


def update_caches(update_cache_entities: typing.Tuple[SubscriptionCacheEntity, ...]):
    """
    Update the cache objects for an update_cache_entity in the database.
    """

    organisations = Organisation.objects.select_related(
        "subscription_information_cache", "subscription"
    ).all()

    organisation_info_cache_dict: typing.Dict[
        int, OrganisationSubscriptionInformationCache
    ] = {
        org.id: getattr(org, "subscription_information_cache", None)
        or OrganisationSubscriptionInformationCache(organisation=org)
        for org in organisations
    }

    if SubscriptionCacheEntity.INFLUX in update_cache_entities:
        _update_caches_with_influx_data(organisation_info_cache_dict)

    if SubscriptionCacheEntity.CHARGEBEE in update_cache_entities:
        _update_caches_with_chargebee_data(organisations, organisation_info_cache_dict)

    to_update = []
    to_create = []

    for subscription_info_cache in organisation_info_cache_dict.values():
        if subscription_info_cache.id:
            to_update.append(subscription_info_cache)
        else:
            to_create.append(subscription_info_cache)

    OrganisationSubscriptionInformationCache.objects.bulk_create(to_create)
    OrganisationSubscriptionInformationCache.objects.bulk_update(
        to_update,
        fields=[
            "api_calls_24h",
            "api_calls_7d",
            "api_calls_30d",
            "allowed_seats",
            "allowed_30d_api_calls",
            "chargebee_email",
            "chargebee_updated_at",
            "influx_updated_at",
        ],
    )


def _update_caches_with_influx_data(
    organisation_info_cache_dict: OrganisationSubscriptionInformationCacheDict,
) -> None:
    """
    Mutates the provided organisation_info_cache_dict in place to add information about the organisation's
    influx usage.
    """
    if not settings.INFLUXDB_TOKEN:
        return

    for date_range, limit in (("30d", ""), ("7d", ""), ("24h", "100")):
        key = f"api_calls_{date_range}"
        org_calls = get_top_organisations(date_range, limit)
        for org_id, calls in org_calls.items():
            subscription_info_cache = organisation_info_cache_dict.get(org_id)
            if not subscription_info_cache:
                # I don't think this is a valid case but worth checking / handling
                continue
            setattr(subscription_info_cache, key, calls)


def _update_caches_with_chargebee_data(
    organisations: typing.Iterable[Organisation],
    organisation_info_cache_dict: OrganisationSubscriptionInformationCacheDict,
):
    """
    Mutates the provided organisation_info_cache_dict in place to add information about the organisation's
    chargebee plan.
    """
    if not settings.CHARGEBEE_API_KEY:
        return

    for organisation in organisations:
        subscription = getattr(organisation, "subscription", None)
        if (
            not subscription
            or subscription.subscription_id is None
            or subscription.payment_method != CHARGEBEE
        ):
            continue

        metadata = get_subscription_metadata_from_id(subscription.subscription_id)
        if not metadata:
            continue

        subscription_info_cache = organisation_info_cache_dict[organisation.id]
        subscription_info_cache.allowed_seats = metadata.seats
        subscription_info_cache.allowed_30d_api_calls = metadata.api_calls
        subscription_info_cache.chargebee_email = metadata.chargebee_email
