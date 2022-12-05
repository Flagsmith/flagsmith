from organisations.chargebee import (
    get_subscription_metadata as get_chargebee_subscription_metadata,
)
from organisations.models import Organisation
from organisations.subscriptions.xero.metadata import XeroSubscriptionMetadata

from .constants import CHARGEBEE, SUBSCRIPTION_DEFAULT_LIMITS
from .metadata import BaseSubscriptionMetadata


def get_subscription_metadata(organisation: Organisation) -> BaseSubscriptionMetadata:
    max_api_calls, max_seats, max_projects = SUBSCRIPTION_DEFAULT_LIMITS
    subscription_metadata = BaseSubscriptionMetadata(
        seats=max_seats, api_calls=max_api_calls, projects=max_projects
    )
    if getattr(organisation, "subscription", None) is not None:
        if organisation.subscription.payment_method == CHARGEBEE:
            chargebee_subscription_metadata = get_chargebee_subscription_metadata(
                organisation.subscription.subscription_id
            )
            if chargebee_subscription_metadata is not None:
                subscription_metadata = chargebee_subscription_metadata
        else:
            subscription_metadata = XeroSubscriptionMetadata(
                seats=organisation.subscription.max_seats,
                api_calls=organisation.subscription.max_api_calls,
            )

    return subscription_metadata
