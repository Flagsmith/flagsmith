import chargebee as chargebee
from django.conf import settings

chargebee.configure(settings.CHARGEBEE_API_KEY, settings.CHARGEBEE_SITE)


def get_max_seats_for_plan(plan_id):
    meta_data = get_plan_meta_data(plan_id)
    return meta_data.get('seats', 0)


def get_plan_meta_data(plan_id):
    plan_details = _get_plan_details(plan_id)
    if hasattr(plan_details.plan, 'meta_data'):
        return plan_details.plan.meta_data
    return {}


def _get_plan_details(plan_id):
    return chargebee.Plan.retrieve(plan_id)


