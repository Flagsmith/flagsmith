import logging

import chargebee as chargebee
from django.conf import settings

chargebee.configure(settings.CHARGEBEE_API_KEY, settings.CHARGEBEE_SITE)

logger = logging.getLogger(__name__)


def get_plan_id_from_subscription(subscription_id):
    if not subscription_id:
        return

    subscription_details = get_subscription_details(subscription_id)

    if subscription_details:
        return subscription_details.subscription.plan_id


def get_subscription_details(subscription_id):
    subscription_details = None

    try:
        subscription_details = chargebee.Subscription.retrieve(subscription_id)
    except chargebee.InvalidRequestError:
        logging.warning('Subscription not found for subscription id %s' % subscription_id)

    return subscription_details


def get_max_seats_for_plan(plan_id):
    meta_data = get_plan_meta_data(plan_id)
    return meta_data.get('seats', 0)


def get_plan_meta_data(plan_id):
    plan_details = get_plan_details(plan_id)
    if plan_details and hasattr(plan_details.plan, 'meta_data'):
        return plan_details.plan.meta_data
    return {}


def get_plan_details(plan_id):
    if plan_id:
        return chargebee.Plan.retrieve(plan_id)
