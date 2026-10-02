from django.conf import settings
from django.utils import timezone

from integrations.flagsmith.client import get_openfeature_client
from organisations.constants import (
    OVERAGE_BILLING_MAX_TERM,
    OVERAGE_BILLING_MIN_TERM,
    OVERAGE_BILLING_PLAN_FAMILIES,
)
from organisations.dataclasses import APILimitRestrictions
from organisations.models import Organisation
from organisations.subscriptions.constants import FREE_PLAN_ID


def get_api_limit_restrictions(organisation: Organisation) -> APILimitRestrictions:
    if not (
        settings.ENABLE_API_USAGE_ALERTING
        and hasattr(organisation, "subscription")
        and organisation.subscription.plan == FREE_PLAN_ID
    ):
        return APILimitRestrictions(
            stop_serving_flags=False,
            block_access_to_admin=False,
        )

    openfeature_client = get_openfeature_client()
    evaluation_context = organisation.openfeature_evaluation_context
    return APILimitRestrictions(
        stop_serving_flags=openfeature_client.get_boolean_value(
            "api_limiting_stop_serving_flags",
            default_value=False,
            evaluation_context=evaluation_context,
        ),
        block_access_to_admin=openfeature_client.get_boolean_value(
            "api_limiting_block_access_to_admin",
            default_value=False,
            evaluation_context=evaluation_context,
        ),
    )


def is_overage_billing_eligible(organisation: Organisation) -> bool:
    if not settings.ENABLE_API_USAGE_ALERTING:
        return False
    if not organisation.has_paid_subscription():
        return False

    subscription = organisation.subscription
    if (
        subscription.subscription_plan_family not in OVERAGE_BILLING_PLAN_FAMILIES
        or subscription.cancellation_date is not None
    ):
        return False
    if not organisation.has_subscription_information_cache():
        return False

    cache = organisation.subscription_information_cache
    starts_at = cache.current_billing_term_starts_at
    ends_at = cache.current_billing_term_ends_at
    if starts_at is None or ends_at is None:
        return False
    if not starts_at <= timezone.now() < ends_at:
        return False
    if not OVERAGE_BILLING_MIN_TERM <= ends_at - starts_at <= OVERAGE_BILLING_MAX_TERM:
        return False

    return get_openfeature_client().get_boolean_value(
        "api_usage_overage_charges",
        default_value=False,
        evaluation_context=organisation.openfeature_evaluation_context,
    )
