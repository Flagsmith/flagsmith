from datetime import timedelta

import pytest
from django.utils import timezone

from organisations.models import (
    Organisation,
    OrganisationSubscriptionInformationCache,
)
from organisations.services import (
    get_api_limit_restrictions,
    is_overage_charging_enabled,
)
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


def _monthly_term(
    organisation: Organisation,
    plan: str = "scale-up-v2",
    term: timedelta = timedelta(days=30),
) -> None:
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        current_billing_term_starts_at=now - term + timedelta(days=1),
        current_billing_term_ends_at=now + timedelta(days=1),
    )
    organisation.subscription.plan = plan
    organisation.subscription.save()


def test_is_overage_charging_enabled__monthly_paid_plan__returns_true(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("api_usage_overage_charges")
    _monthly_term(organisation)

    # When / Then
    assert is_overage_charging_enabled(organisation) is True


def test_is_overage_charging_enabled__flag_off__returns_false(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features()
    _monthly_term(organisation)

    # When / Then
    assert is_overage_charging_enabled(organisation) is False


@pytest.mark.parametrize("plan", [FREE_PLAN_ID, "enterprise"])
def test_is_overage_charging_enabled__unbilled_plan__returns_false(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
    plan: str,
) -> None:
    # Given
    enable_features("api_usage_overage_charges")
    _monthly_term(organisation, plan=plan)

    # When / Then
    assert is_overage_charging_enabled(organisation) is False


# The overage task only bills terms roughly a month long.
def test_is_overage_charging_enabled__annual_term__returns_false(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("api_usage_overage_charges")
    _monthly_term(organisation, term=timedelta(days=365))

    # When / Then
    assert is_overage_charging_enabled(organisation) is False


def test_is_overage_charging_enabled__cancelled__returns_false(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("api_usage_overage_charges")
    _monthly_term(organisation)
    organisation.subscription.cancellation_date = timezone.now()
    organisation.subscription.save()

    # When / Then
    assert is_overage_charging_enabled(organisation) is False


def test_is_overage_charging_enabled__no_subscription_cache__returns_false(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("api_usage_overage_charges")
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()

    # When / Then
    assert is_overage_charging_enabled(organisation) is False


def test_is_overage_charging_enabled__no_billing_term__returns_false(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("api_usage_overage_charges")
    OrganisationSubscriptionInformationCache.objects.create(organisation=organisation)
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()

    # When / Then
    assert is_overage_charging_enabled(organisation) is False


def test_is_overage_charging_enabled__term_has_ended__returns_false(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("api_usage_overage_charges")
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        current_billing_term_starts_at=now - timedelta(days=60),
        current_billing_term_ends_at=now - timedelta(days=30),
    )
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()

    # When / Then
    assert is_overage_charging_enabled(organisation) is False


def test_is_overage_charging_enabled__no_subscription__returns_false(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("api_usage_overage_charges")
    organisation.subscription.hard_delete()
    organisation = Organisation.objects.get(pk=organisation.pk)

    # When / Then
    assert is_overage_charging_enabled(organisation) is False
