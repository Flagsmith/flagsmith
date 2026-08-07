import typing

from integrations.flagsmith.client import get_openfeature_client
from organisations.models import Organisation

OnboardingVariant = typing.Literal["control", "single_page"]


def get_onboarding_variant(organisation: Organisation) -> OnboardingVariant:
    details = get_openfeature_client().get_boolean_details(
        "onboarding_quickstart_flow",
        default_value=False,
        evaluation_context=organisation.openfeature_evaluation_context,
    )
    if not details.value or details.variant == "control":
        return "control"
    return "single_page"
