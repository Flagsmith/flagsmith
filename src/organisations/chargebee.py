import logging
from datetime import datetime

import chargebee as chargebee
from django.conf import settings
from pytz import UTC

chargebee.configure(settings.CHARGEBEE_API_KEY, settings.CHARGEBEE_SITE)

logger = logging.getLogger(__name__)


def get_subscription_data_from_hosted_page(hosted_page_id):
    hosted_page = get_hosted_page(hosted_page_id)
    subscription = get_subscription_from_hosted_page(hosted_page)
    if subscription:
        return {
            "subscription_id": subscription.id,
            "plan": subscription.plan_id,
            "subscription_date": datetime.fromtimestamp(
                subscription.created_at, tz=UTC
            ),
            "max_seats": get_max_seats_for_plan(subscription.plan_id),
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


def get_max_seats_for_plan(plan_id):
    meta_data = get_plan_meta_data(plan_id)
    return meta_data.get("seats", 1)


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
