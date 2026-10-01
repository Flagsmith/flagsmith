from integrations.flagsmith.client import get_openfeature_client
from organisations.dataclasses import APILimitRestrictions
from organisations.models import Organisation
from organisations.subscriptions.constants import FREE_PLAN_ID


def get_api_limit_restrictions(organisation: Organisation) -> APILimitRestrictions:
    if (
        not hasattr(organisation, "subscription")
        or organisation.subscription.plan != FREE_PLAN_ID
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
