from datetime import datetime

import chargebee
from django.conf import settings
from pytz import UTC

from .cache import ChargebeeCache
from .metadata import ChargebeeObjMetadata

chargebee.configure(settings.CHARGEBEE_API_KEY, settings.CHARGEBEE_SITE)


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


def get_subscription_metadata(subscription_id: str) -> ChargebeeObjMetadata:
    subscription = chargebee.Subscription.retrieve(subscription_id).subscription
    addon_ids = (
        [addon.id for addon in subscription.addons] if subscription.addons else []
    )

    chargebee_cache = ChargebeeCache()
    plan_metadata = chargebee_cache.plans[subscription.plan_id]
    subscription_metadata = plan_metadata

    for addon_id in addon_ids:
        addon_metadata = chargebee_cache.addons[addon_id]
        subscription_metadata = subscription_metadata + addon_metadata

    return subscription_metadata
