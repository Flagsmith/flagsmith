from datetime import datetime, timedelta

import pytest
from django.utils import timezone

from organisations.models import (
    Organisation,
    OrganisationBreachedGracePeriod,
    OrganisationSubscriptionInformationCache,
)
from organisations.services import (
    has_used_overage_grace,
    is_overage_charging_enabled,
)
from organisations.subscriptions.constants import FREE_PLAN_ID
from tests.types import EnableFeaturesFixture


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
    organisation.subscription.subscription_id = "sub-1"
    organisation.subscription.save()


def _grace_row(organisation: Organisation, created_at: datetime) -> None:
    row = OrganisationBreachedGracePeriod.objects.create(organisation=organisation)
    # created_at is auto_now_add, so it can only be placed after the fact.
    OrganisationBreachedGracePeriod.objects.filter(pk=row.pk).update(
        created_at=created_at
    )


@pytest.mark.parametrize(
    "plan, expected",
    [
        ("scale-up-v2", True),
        ("startup-v2", True),
        # A free organisation's row is the wait before flags stop, not an
        # overage month, and an enterprise plan has neither.
        (FREE_PLAN_ID, False),
        ("enterprise", False),
    ],
)
def test_has_used_overage_grace__row_from_an_earlier_term__reads_it_per_plan(
    organisation: Organisation,
    plan: str,
    expected: bool,
) -> None:
    # Given
    _monthly_term(organisation, plan=plan)
    _grace_row(organisation, created_at=timezone.now() - timedelta(days=60))

    # When / Then
    assert has_used_overage_grace(organisation) is expected


# The forgiven month is happening now, so this term is still covered.
def test_has_used_overage_grace__row_from_this_term__returns_false(
    organisation: Organisation,
) -> None:
    # Given
    _monthly_term(organisation)
    _grace_row(organisation, created_at=timezone.now() - timedelta(hours=1))

    # When / Then
    assert has_used_overage_grace(organisation) is False


def test_has_used_overage_grace__no_breached_row__returns_false(
    organisation: Organisation,
) -> None:
    # Given
    _monthly_term(organisation)

    # When / Then
    assert has_used_overage_grace(organisation) is False


# Without a term we cannot say which one the row belongs to.
def test_has_used_overage_grace__no_subscription_cache__returns_false(
    organisation: Organisation,
) -> None:
    # Given
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()
    _grace_row(organisation, created_at=timezone.now() - timedelta(days=60))

    # When / Then
    assert has_used_overage_grace(organisation) is False


# A cache can exist before Chargebee has written a term to it.
def test_has_used_overage_grace__no_billing_term__returns_false(
    organisation: Organisation,
) -> None:
    # Given
    OrganisationSubscriptionInformationCache.objects.create(organisation=organisation)
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()
    _grace_row(organisation, created_at=timezone.now() - timedelta(days=60))

    # When / Then
    assert has_used_overage_grace(organisation) is False


def test_has_used_overage_grace__no_subscription__returns_false(
    organisation: Organisation,
) -> None:
    # Given
    _grace_row(organisation, created_at=timezone.now() - timedelta(days=60))
    organisation.subscription.hard_delete()
    organisation = Organisation.objects.get(pk=organisation.pk)

    # When / Then
    assert has_used_overage_grace(organisation) is False


# The plan change hook deletes the row without clearing the cached relation.
def test_has_used_overage_grace__read_before_plan_change__rereads_the_row(
    organisation: Organisation,
) -> None:
    # Given
    _monthly_term(organisation)
    _grace_row(organisation, created_at=timezone.now() - timedelta(days=60))
    assert has_used_overage_grace(organisation) is True

    # When
    organisation.subscription.plan = "startup-v2"
    organisation.subscription.save()

    # Then
    assert has_used_overage_grace(organisation) is False


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


def test_is_overage_charging_enabled__no_chargebee_subscription__returns_false(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("api_usage_overage_charges")
    _monthly_term(organisation)
    organisation.subscription.subscription_id = None
    organisation.subscription.save()

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
    organisation.subscription.subscription_id = "sub-1"
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
    organisation.subscription.subscription_id = "sub-1"
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
    organisation.subscription.subscription_id = "sub-1"
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
