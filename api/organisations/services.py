from dataclasses import dataclass

from integrations.flagsmith.client import get_openfeature_client
from organisations.models import Organisation
from organisations.subscriptions.constants import FREE_PLAN_ID


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
