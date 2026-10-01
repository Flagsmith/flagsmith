import pytest

from organisations.dataclasses import APILimitRestrictions
from organisations.models import Organisation
from organisations.services import get_api_limit_restrictions
from organisations.subscriptions.constants import FREE_PLAN_ID
from tests.types import EnableFeaturesFixture


@pytest.mark.parametrize(
    "plan, enabled_features, expected_restrictions",
    [
        (FREE_PLAN_ID, (), APILimitRestrictions(False, False)),
        (
            FREE_PLAN_ID,
            ("api_limiting_stop_serving_flags",),
            APILimitRestrictions(True, False),
        ),
        (
            FREE_PLAN_ID,
            ("api_limiting_block_access_to_admin",),
            APILimitRestrictions(False, True),
        ),
        (
            FREE_PLAN_ID,
            (
                "api_limiting_stop_serving_flags",
                "api_limiting_block_access_to_admin",
            ),
            APILimitRestrictions(True, True),
        ),
        (
            "scale-up-v2",
            (
                "api_limiting_stop_serving_flags",
                "api_limiting_block_access_to_admin",
            ),
            APILimitRestrictions(False, False),
        ),
    ],
)
def test_get_api_limit_restrictions__plan_and_flags__returns_expected(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
    plan: str,
    enabled_features: tuple[str, ...],
    expected_restrictions: APILimitRestrictions,
) -> None:
    # Given
    organisation.subscription.plan = plan
    organisation.subscription.save()
    enable_features(*enabled_features)

    # When
    restrictions = get_api_limit_restrictions(organisation)

    # Then
    assert restrictions == expected_restrictions
    assert restrictions.enabled is (
        expected_restrictions.stop_serving_flags
        or expected_restrictions.block_access_to_admin
    )


def test_get_api_limit_restrictions__no_subscription__returns_no_restrictions(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(
        "api_limiting_stop_serving_flags",
        "api_limiting_block_access_to_admin",
    )
    organisation.subscription.hard_delete()
    organisation = Organisation.objects.get(id=organisation.id)

    # When
    restrictions = get_api_limit_restrictions(organisation)

    # Then
    assert restrictions == APILimitRestrictions(False, False)
