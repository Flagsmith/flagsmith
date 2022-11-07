import typing

from app_analytics.influxdb_wrapper import get_top_organisations
from django.conf import settings

from .chargebee import get_subscription_metadata
from .subscriptions.constants import CHARGEBEE

if typing.TYPE_CHECKING:
    from .models import Organisation, OrganisationSubscriptionInformationCache

    OrganisationSubscriptionInformationCacheDict = typing.Dict[
        int, OrganisationSubscriptionInformationCache
    ]


def update_caches_with_influx_data(
    organisation_info_cache_dict: "OrganisationSubscriptionInformationCacheDict",
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
                # TODO: I don't think this is a valid case but worth checking / handling
                continue
            setattr(subscription_info_cache, key, calls)


def update_caches_with_chargebee_data(
    organisations: typing.Iterable["Organisation"],
    organisation_info_cache_dict: "OrganisationSubscriptionInformationCacheDict",
):
    """
    Mutates the provided organisation_info_cache_dict in place to add information about the organisation's
    chargebee plan information.
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

        metadata = get_subscription_metadata(subscription.subscription_id)
        if not metadata:
            continue

        subscription_info_cache = organisation_info_cache_dict[organisation.id]
        subscription_info_cache.allowed_seats = metadata.seats
        subscription_info_cache.allowed_30d_api_calls = metadata.api_calls
