from organisations.chargebee import (
    get_subscription_metadata as get_chargebee_subscription_metadata,
)
from organisations.models import Organisation

from .constants import CHARGEBEE, SUBSCRIPTION_DEFAULT_LIMITS
from .metadata import BaseSubscriptionMetadata


def get_subscription_metadata(organisation: Organisation) -> BaseSubscriptionMetadata:
    max_api_calls, max_seats, max_projects = SUBSCRIPTION_DEFAULT_LIMITS
    if getattr(organisation, "subscription", None) is not None:
        if organisation.subscription.payment_method == CHARGEBEE:
            subscription_metadata = get_chargebee_subscription_metadata(
                organisation.subscription.subscription_id
            )
            max_api_calls = getattr(subscription_metadata, "api_calls", max_api_calls)
            max_seats = getattr(subscription_metadata, "seats", max_seats)
            max_projects = getattr(subscription_metadata, "projects", max_projects)
        else:
            max_api_calls = organisation.subscription.max_api_calls
            max_seats = organisation.subscription.max_seats
            max_projects = None

    return BaseSubscriptionMetadata(
        seats=max_seats, api_calls=max_api_calls, projects=max_projects
    )
