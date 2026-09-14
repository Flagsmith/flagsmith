import pytest

from organisations.models import Organisation
from organisations.services import get_api_limit_restrictions
from organisations.subscriptions.constants import FREE_PLAN_ID
from tests.types import EnableFeaturesFixture


def test_get_api_limit_restrictions__free_plan_both_flags__returns_both_enabled(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(
        "api_limiting_stop_serving_flags",
        "api_limiting_block_access_to_admin",
    )

    # When
    restrictions = get_api_limit_restrictions(organisation)

    # Then
    assert restrictions.stop_serving_flags is True
    assert restrictions.block_access_to_admin is True
    assert restrictions.enabled is True


@pytest.mark.parametrize(
    "feature_name, expected_stop_serving, expected_block_access",
    [
        ("api_limiting_stop_serving_flags", True, False),
        ("api_limiting_block_access_to_admin", False, True),
    ],
)
def test_get_api_limit_restrictions__free_plan_one_flag__returns_only_that_one(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
    feature_name: str,
    expected_stop_serving: bool,
    expected_block_access: bool,
) -> None:
    # Given
    enable_features(feature_name)

    # When
    restrictions = get_api_limit_restrictions(organisation)

    # Then
    assert restrictions.stop_serving_flags is expected_stop_serving
    assert restrictions.block_access_to_admin is expected_block_access
    assert restrictions.enabled is True


def test_get_api_limit_restrictions__free_plan_no_flags__returns_none_enabled(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features()

    # When
    restrictions = get_api_limit_restrictions(organisation)

    # Then
    assert restrictions.stop_serving_flags is False
    assert restrictions.block_access_to_admin is False
    assert restrictions.enabled is False


@pytest.mark.parametrize("plan", ["scale-up-v2", "start-up-v2", "enterprise"])
def test_get_api_limit_restrictions__paid_plan__returns_none_enabled(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
    plan: str,
) -> None:
    # Given
    enable_features(
        "api_limiting_stop_serving_flags",
        "api_limiting_block_access_to_admin",
    )
    organisation.subscription.plan = plan
    organisation.subscription.save()

    # When
    restrictions = get_api_limit_restrictions(organisation)

    # Then
    assert restrictions.enabled is False


# A null plan is free by every other measure, but the restriction task filters
# on the plan id, so such an organisation is never cut off.
def test_get_api_limit_restrictions__no_plan__returns_none_enabled(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(
        "api_limiting_stop_serving_flags",
        "api_limiting_block_access_to_admin",
    )
    organisation.subscription.plan = None
    organisation.subscription.save()

    # When
    restrictions = get_api_limit_restrictions(organisation)

    # Then
    assert restrictions.enabled is False


def test_get_api_limit_restrictions__no_subscription__returns_none_enabled(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(
        "api_limiting_stop_serving_flags",
        "api_limiting_block_access_to_admin",
    )
    assert organisation.subscription.plan == FREE_PLAN_ID
    # A soft delete leaves the relation resolvable, and refresh_from_db keeps
    # the cached one, so remove the row and re-fetch.
    organisation.subscription.hard_delete()
    organisation = Organisation.objects.get(pk=organisation.pk)

    # When
    restrictions = get_api_limit_restrictions(organisation)

    # Then
    assert restrictions.enabled is False
