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

BOTH_RESTRICTION_FLAGS = (
    "api_limiting_stop_serving_flags",
    "api_limiting_block_access_to_admin",
)
NO_RESTRICTIONS = APILimitRestrictions(
    stop_serving_flags=False,
    block_access_to_admin=False,
)


@pytest.mark.parametrize(
    "plan, alerting_enabled, enabled_features, expected_restrictions",
    [
        pytest.param(FREE_PLAN_ID, True, (), NO_RESTRICTIONS, id="free-no-flags"),
        pytest.param(
            FREE_PLAN_ID,
            True,
            ("api_limiting_stop_serving_flags",),
            APILimitRestrictions(stop_serving_flags=True, block_access_to_admin=False),
            id="free-stop-serving-flags",
        ),
        pytest.param(
            FREE_PLAN_ID,
            True,
            ("api_limiting_block_access_to_admin",),
            APILimitRestrictions(stop_serving_flags=False, block_access_to_admin=True),
            id="free-block-access-to-admin",
        ),
        pytest.param(
            FREE_PLAN_ID,
            True,
            BOTH_RESTRICTION_FLAGS,
            APILimitRestrictions(stop_serving_flags=True, block_access_to_admin=True),
            id="free-both-flags",
        ),
        pytest.param(
            "scale-up-v2",
            True,
            BOTH_RESTRICTION_FLAGS,
            NO_RESTRICTIONS,
            id="paid-both-flags",
        ),
        pytest.param(
            FREE_PLAN_ID,
            False,
            BOTH_RESTRICTION_FLAGS,
            NO_RESTRICTIONS,
            id="free-alerting-disabled",
        ),
    ],
)
def test_get_api_limit_restrictions__plan_and_flags__returns_expected(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
    settings: SettingsWrapper,
    plan: str,
    alerting_enabled: bool,
    enabled_features: tuple[str, ...],
    expected_restrictions: APILimitRestrictions,
) -> None:
    # Given
    settings.ENABLE_API_USAGE_ALERTING = alerting_enabled
    organisation.subscription.plan = plan
    organisation.subscription.save()
    enable_features(*enabled_features)

    # When
    restrictions = get_api_limit_restrictions(organisation)

    # Then
    assert restrictions == expected_restrictions


def test_get_api_limit_restrictions__no_subscription__returns_no_restrictions(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ENABLE_API_USAGE_ALERTING = True
    enable_features(*BOTH_RESTRICTION_FLAGS)
    organisation.subscription.hard_delete()
    organisation.refresh_from_db()

    # When
    restrictions = get_api_limit_restrictions(organisation)

    # Then
    assert restrictions == NO_RESTRICTIONS


@pytest.mark.parametrize(
    "missing, expected",
    [
        pytest.param(None, True, id="eligible"),
        pytest.param("subscription", False, id="no-subscription"),
        pytest.param("subscription_id", False, id="no-subscription-id"),
        pytest.param("cache", False, id="no-subscription-cache"),
        pytest.param("billing_term", False, id="no-billing-term"),
        pytest.param("billing_period", False, id="billing-term-ended"),
        pytest.param("alerting_setting", False, id="alerting-disabled"),
    ],
)
def test_is_overage_billing_eligible__eligibility__returns_expected(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
    settings: SettingsWrapper,
    missing: str | None,
    expected: bool,
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
    if missing == "billing_term":
        OrganisationSubscriptionInformationCache.objects.create(
            organisation=organisation,
            allowed_30d_api_calls=100_000,
        )
    elif missing != "cache":
        now = timezone.now()
        OrganisationSubscriptionInformationCache.objects.create(
            organisation=organisation,
            allowed_30d_api_calls=100_000,
            current_billing_term_starts_at=now - timedelta(days=29),
            current_billing_term_ends_at=(
                now - timedelta(days=1)
                if missing == "billing_period"
                else now + timedelta(days=1)
            ),
        )
    organisation.refresh_from_db()

    # When
    eligible = is_overage_billing_eligible(organisation)

    # Then
    assert eligible is expected
