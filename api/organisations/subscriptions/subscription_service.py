from organisations.chargebee import get_subscription_metadata_from_id
from organisations.models import Organisation
from organisations.subscriptions.xero.metadata import XeroSubscriptionMetadata

from .constants import CHARGEBEE, SUBSCRIPTION_DEFAULT_LIMITS, XERO
from .metadata import BaseSubscriptionMetadata


def get_subscription_metadata(organisation: Organisation) -> BaseSubscriptionMetadata:
    max_api_calls, max_seats, max_projects = SUBSCRIPTION_DEFAULT_LIMITS
    subscription_metadata = BaseSubscriptionMetadata(
        seats=max_seats, api_calls=max_api_calls, projects=max_projects
    )
    if organisation.subscription.payment_method == CHARGEBEE:
        chargebee_subscription_metadata = get_subscription_metadata_from_id(
            organisation.subscription.subscription_id
        )
        if chargebee_subscription_metadata is not None:
            subscription_metadata = chargebee_subscription_metadata
    elif organisation.subscription.payment_method == XERO:
        subscription_metadata = XeroSubscriptionMetadata(
            seats=organisation.subscription.max_seats,
            api_calls=organisation.subscription.max_api_calls,
        )

    return subscription_metadata
