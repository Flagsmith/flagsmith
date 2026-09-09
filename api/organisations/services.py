from dataclasses import dataclass
from datetime import timedelta

from integrations.flagsmith.client import get_openfeature_client
from organisations.models import Organisation
from organisations.subscriptions.constants import (
    FREE_PLAN_ID,
    SubscriptionPlanFamily,
)

# Mirrors charge_for_api_call_count_overages, which only bills terms roughly a
# month long, so an annual subscription is never charged for an overage.
MONTHLY_TERM_MIN = timedelta(days=25)
MONTHLY_TERM_MAX = timedelta(days=35)

CHARGEABLE_PLAN_FAMILIES = (
    SubscriptionPlanFamily.START_UP,
    SubscriptionPlanFamily.SCALE_UP,
)


@dataclass(frozen=True)
class APILimitRestrictions:
    stop_serving_flags: bool
    block_access_to_admin: bool

    @property
    def enabled(self) -> bool:
        return self.stop_serving_flags or self.block_access_to_admin


NO_RESTRICTIONS = APILimitRestrictions(
    stop_serving_flags=False,
    block_access_to_admin=False,
)


def get_api_limit_restrictions(organisation: Organisation) -> APILimitRestrictions:
    """
    Return the restrictions that apply to an organisation which stays over its
    API limit. Both are off for an organisation that is never restricted.
    """
    # Matches the queryset in restrict_use_due_to_api_limit_grace_period_over,
    # which filters on the plan id rather than the plan family, so an
    # organisation with no plan set is left alone.
    if not hasattr(organisation, "subscription"):
        return NO_RESTRICTIONS
    if organisation.subscription.plan != FREE_PLAN_ID:
        return NO_RESTRICTIONS

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


def is_overage_charging_enabled(organisation: Organisation) -> bool:
    """
    Whether going over the API limit can put a charge on this organisation's
    next invoice.
    """
    if not hasattr(organisation, "subscription"):
        return False

    subscription = organisation.subscription
    if subscription.subscription_plan_family not in CHARGEABLE_PLAN_FAMILIES:
        return False
    if subscription.cancellation_date is not None:
        return False
    if not organisation.has_subscription_information_cache():
        return False

    cache = organisation.subscription_information_cache
    starts_at = cache.current_billing_term_starts_at
    ends_at = cache.current_billing_term_ends_at
    if starts_at is None or ends_at is None:
        return False
    if not cache.has_active_billing_periods():
        return False
    if not MONTHLY_TERM_MIN <= ends_at - starts_at <= MONTHLY_TERM_MAX:
        return False

    return get_openfeature_client().get_boolean_value(
        "api_usage_overage_charges",
        default_value=False,
        evaluation_context=organisation.openfeature_evaluation_context,
    )
