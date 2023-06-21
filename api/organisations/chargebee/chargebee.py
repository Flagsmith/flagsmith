import logging
import typing
from contextlib import suppress
from datetime import datetime

import chargebee
from chargebee import APIError as ChargebeeAPIError
from django.conf import settings
from pytz import UTC

from ..subscriptions.constants import CHARGEBEE
from ..subscriptions.exceptions import (
    CannotCancelChargebeeSubscription,
    UpgradeSeatsError,
)
from .cache import ChargebeeCache
from .constants import ADDITIONAL_SEAT_ADDON_ID
from .metadata import ChargebeeObjMetadata

chargebee.configure(settings.CHARGEBEE_API_KEY, settings.CHARGEBEE_SITE)

logger = logging.getLogger(__name__)


def get_subscription_data_from_hosted_page(hosted_page_id):
    hosted_page = get_hosted_page(hosted_page_id)
    subscription = get_subscription_from_hosted_page(hosted_page)
    plan_metadata = get_plan_meta_data(subscription.plan_id)
    if subscription:
        return {
            "subscription_id": subscription.id,
            "plan": subscription.plan_id,
            "subscription_date": datetime.fromtimestamp(
                subscription.created_at, tz=UTC
            ),
            "max_seats": get_max_seats_for_plan(plan_metadata),
            "max_api_calls": get_max_api_calls_for_plan(plan_metadata),
            "customer_id": get_customer_id_from_hosted_page(hosted_page),
            "payment_method": CHARGEBEE,
        }
    else:
        return {}


def get_hosted_page(hosted_page_id):
    response = chargebee.HostedPage.retrieve(hosted_page_id)
    return response.hosted_page


def get_subscription_from_hosted_page(hosted_page):
    if hasattr(hosted_page, "content"):
        content = hosted_page.content
        if hasattr(content, "subscription"):
            return content.subscription


def get_customer_id_from_hosted_page(hosted_page):
    if hasattr(hosted_page, "content"):
        content = hosted_page.content
        if hasattr(content, "customer"):
            return content.customer.id


def get_max_seats_for_plan(meta_data: dict) -> int:
    return meta_data.get("seats", 1)


def get_max_api_calls_for_plan(meta_data: dict) -> int:
    return meta_data.get("api_calls", 50000)


def get_plan_meta_data(plan_id):
    plan_details = get_plan_details(plan_id)
    if plan_details and hasattr(plan_details.plan, "meta_data"):
        return plan_details.plan.meta_data or {}
    return {}


def get_plan_details(plan_id):
    if plan_id:
        return chargebee.Plan.retrieve(plan_id)


def get_portal_url(customer_id, redirect_url):
    result = chargebee.PortalSession.create(
        {"redirect_url": redirect_url, "customer": {"id": customer_id}}
    )
    if result and hasattr(result, "portal_session"):
        return result.portal_session.access_url


def get_customer_id_from_subscription_id(subscription_id):
    subscription_response = chargebee.Subscription.retrieve(subscription_id)
    if hasattr(subscription_response, "customer"):
        return subscription_response.customer.id


def get_hosted_page_url_for_subscription_upgrade(
    subscription_id: str, plan_id: str
) -> str:
    params = {"subscription": {"id": subscription_id, "plan_id": plan_id}}
    checkout_existing_response = chargebee.HostedPage.checkout_existing(params)
    return checkout_existing_response.hosted_page.url


def get_subscription_metadata(
    subscription_id: str,
) -> typing.Optional[ChargebeeObjMetadata]:
    if not (subscription_id and subscription_id.strip() != ""):
        logger.warning("Subscription id is empty or None")
        return None

    with suppress(ChargebeeAPIError):
        chargebee_result = chargebee.Subscription.retrieve(subscription_id)
        subscription = chargebee_result.subscription
        addons = subscription.addons or []

        chargebee_cache = ChargebeeCache()
        plan_metadata = chargebee_cache.plans[subscription.plan_id]
        subscription_metadata = plan_metadata
        subscription_metadata.chargebee_email = chargebee_result.customer.email

        for addon in addons:
            quantity = getattr(addon, "quantity", None) or 1
            addon_metadata = chargebee_cache.addons[addon.id] * quantity
            subscription_metadata = subscription_metadata + addon_metadata

        return subscription_metadata


def cancel_subscription(subscription_id: str):
    try:
        chargebee.Subscription.cancel(subscription_id, {"end_of_term": True})
    except ChargebeeAPIError as e:
        msg = "Cannot cancel CB subscription for subscription id: %s" % subscription_id
        logger.error(msg)
        raise CannotCancelChargebeeSubscription(msg) from e


def add_single_seat(subscription_id: str):
    try:
        subscription = chargebee.Subscription.retrieve(subscription_id).subscription
        addons = subscription.addons or []

        current_seats = next(
            (
                addon.quantity
                for addon in addons
                if addon.id == ADDITIONAL_SEAT_ADDON_ID
            ),
            0,
        )

        chargebee.Subscription.update(
            subscription_id,
            {
                "addons": [
                    {"id": ADDITIONAL_SEAT_ADDON_ID, "quantity": current_seats + 1}
                ],
                "prorate": True,
                "invoice_immediately": True,
            },
        )

    except ChargebeeAPIError as e:
        msg = (
            "Failed to add additional seat to CB subscription for subscription id: %s"
            % subscription_id
        )
        logger.error(msg)
        raise UpgradeSeatsError(msg) from e
