from datetime import timedelta

from integrations.flagsmith.client import get_openfeature_client
from organisations.models import Organisation, OrganisationBreachedGracePeriod
from organisations.subscriptions.constants import SubscriptionPlanFamily

# charge_for_api_call_count_overages only bills terms roughly a month long, so
# an annual subscription is never charged for an overage.
MONTHLY_TERM_MIN = timedelta(days=25)
MONTHLY_TERM_MAX = timedelta(days=35)

CHARGEABLE_PLAN_FAMILIES = (
    SubscriptionPlanFamily.START_UP,
    SubscriptionPlanFamily.SCALE_UP,
)


def _plan_family(organisation: Organisation) -> SubscriptionPlanFamily | None:
    if not hasattr(organisation, "subscription"):
        return None
    return organisation.subscription.subscription_plan_family


def has_used_overage_grace(organisation: Organisation) -> bool:
    """
    Whether the overage month we do not charge for was spent in an earlier
    billing term, which is what makes this term's overage chargeable. A row
    written during this term is the forgiven month happening now.

    A breached grace period row says this on a paid plan and says the wait
    before flags stop on a free one, so the plan decides how to read it. The
    row is cleared when an organisation moves between the two.
    """
    if _plan_family(organisation) not in CHARGEABLE_PLAN_FAMILIES:
        return False
    if not organisation.has_subscription_information_cache():
        return False

    term_starts_at = (
        organisation.subscription_information_cache.current_billing_term_starts_at
    )
    if term_starts_at is None:
        return False

    # Queried rather than read off the instance: the plan change hook deletes
    # the row without clearing Django's cached reverse relation.
    return OrganisationBreachedGracePeriod.objects.filter(
        organisation=organisation,
        created_at__lt=term_starts_at,
    ).exists()


def is_overage_charging_enabled(organisation: Organisation) -> bool:
    """Whether an overage can put a charge on this organisation's next invoice."""
    if _plan_family(organisation) not in CHARGEABLE_PLAN_FAMILIES:
        return False

    if not organisation.has_paid_subscription():
        return False
    if organisation.subscription.cancellation_date is not None:
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
