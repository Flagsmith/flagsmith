from datetime import timedelta

import pytest
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper

from organisations.dataclasses import APILimitRestrictions
from organisations.models import (
    Organisation,
    OrganisationSubscriptionInformationCache,
)
from organisations.services import (
    get_api_limit_restrictions,
    is_overage_billing_eligible,
)
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


@pytest.mark.parametrize(
    "missing",
    ["subscription", "subscription_id", "cache", "billing_period", "alerting_setting"],
)
def test_is_overage_billing_eligible__missing_billing_data__returns_false(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
    settings: SettingsWrapper,
    missing: str,
) -> None:
    # Given
    settings.ENABLE_API_USAGE_ALERTING = missing != "alerting_setting"
    enable_features("api_usage_overage_charges")
    organisation.subscription.plan = "startup-v2"
    organisation.subscription.subscription_id = (
        None if missing == "subscription_id" else "sub_id"
    )
    organisation.subscription.save()
    if missing == "subscription":
        organisation.subscription.hard_delete()
    if missing != "cache":
        now = timezone.now()
        OrganisationSubscriptionInformationCache.objects.create(
            organisation=organisation,
            allowed_30d_api_calls=100_000,
            current_billing_term_starts_at=now - timedelta(days=31),
            current_billing_term_ends_at=(
                now - timedelta(days=1)
                if missing == "billing_period"
                else now + timedelta(days=1)
            ),
        )
    organisation = Organisation.objects.get(id=organisation.id)

    # When
    eligible = is_overage_billing_eligible(organisation)

    # Then
    assert eligible is False
