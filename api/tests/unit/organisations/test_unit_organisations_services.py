import openfeature.api as openfeature_api
from openfeature.provider.in_memory_provider import InMemoryFlag, InMemoryProvider

from integrations.flagsmith.client import DEFAULT_OPENFEATURE_DOMAIN
from organisations.models import Organisation
from organisations.services import get_onboarding_variant


def test_get_onboarding_variant__flag_not_configured__returns_control(
    organisation: Organisation,
) -> None:
    # Given
    # the flag doesn't exist

    # When / Then
    assert get_onboarding_variant(organisation) == "control"


def test_get_onboarding_variant__flag_disabled__returns_control(
    organisation: Organisation,
) -> None:
    # Given
    openfeature_api.set_provider(
        InMemoryProvider(
            {
                "onboarding_quickstart_flow": InMemoryFlag(
                    variants={"off": False},
                    default_variant="off",
                )
            }
        ),
        domain=DEFAULT_OPENFEATURE_DOMAIN,
    )

    # When / Then
    assert get_onboarding_variant(organisation) == "control"


def test_get_onboarding_variant__variant_assigned__returns_single_page(
    organisation: Organisation,
) -> None:
    # Given
    openfeature_api.set_provider(
        InMemoryProvider(
            {
                "onboarding_quickstart_flow": InMemoryFlag(
                    variants={"control": True, "single_page": True},
                    default_variant="single_page",
                )
            }
        ),
        domain=DEFAULT_OPENFEATURE_DOMAIN,
    )

    # When / Then
    assert get_onboarding_variant(organisation) == "single_page"


def test_get_onboarding_variant__control_variant_assigned__returns_control(
    organisation: Organisation,
) -> None:
    # Given
    openfeature_api.set_provider(
        InMemoryProvider(
            {
                "onboarding_quickstart_flow": InMemoryFlag(
                    variants={"control": True, "single_page": True},
                    default_variant="control",
                )
            }
        ),
        domain=DEFAULT_OPENFEATURE_DOMAIN,
    )

    # When / Then
    assert get_onboarding_variant(organisation) == "control"
