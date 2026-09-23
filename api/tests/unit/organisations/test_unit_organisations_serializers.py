from datetime import timedelta

from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from organisations.models import (
    Organisation,
    OrganisationBreachedGracePeriod,
    OrganisationSubscriptionInformationCache,
)
from organisations.serializers import (
    OrganisationSerializerFull,
    UpdateSubscriptionSerializer,
)
from tests.types import EnableFeaturesFixture


def test_organisation_serializer_full__create_with_targeting_key__persists_write_only(
    db: None,
) -> None:
    # Given
    serializer = OrganisationSerializerFull(
        data={"name": "Test Org", "targeting_key": "a" * 32}
    )

    # When
    serializer.is_valid(raise_exception=True)
    organisation = serializer.save()

    # Then
    assert organisation.targeting_key == "a" * 32
    assert "targeting_key" not in serializer.data


def test_organisation_serializer_full__update_targeting_key__ignored(
    organisation: Organisation,
) -> None:
    # Given
    organisation.targeting_key = "a" * 32
    organisation.save(update_fields=["targeting_key"])

    serializer = OrganisationSerializerFull(
        instance=organisation,
        data={"name": organisation.name, "targeting_key": "b" * 32},
    )

    # When
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # Then
    organisation.refresh_from_db()
    assert organisation.targeting_key == "a" * 32


def test_organisation_serializer_full__monthly_paid_plan__reports_overage_state(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("api_usage_overage_charges")
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        current_billing_term_starts_at=now - timedelta(days=29),
        current_billing_term_ends_at=now + timedelta(days=1),
    )
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.subscription_id = "sub-1"
    organisation.subscription.save()

    # When
    data = OrganisationSerializerFull(instance=organisation).data

    # Then
    assert data["overage_charges_enabled"] is True
    assert data["overage_grace_period_used"] is False


def test_organisation_serializer_full__paid_plan_grace_spent__reports_it(
    organisation: Organisation,
) -> None:
    # Given
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        current_billing_term_starts_at=now - timedelta(days=29),
        current_billing_term_ends_at=now + timedelta(days=1),
    )
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()
    row = OrganisationBreachedGracePeriod.objects.create(organisation=organisation)
    OrganisationBreachedGracePeriod.objects.filter(pk=row.pk).update(
        created_at=now - timedelta(days=60)
    )

    # When
    data = OrganisationSerializerFull(instance=organisation).data

    # Then
    assert data["overage_grace_period_used"] is True


# A free organisation's row is the wait before flags stop, not an overage month.
def test_organisation_serializer_full__free_plan_grace_spent__reports_overage_unused(
    organisation: Organisation,
) -> None:
    # Given
    OrganisationBreachedGracePeriod.objects.create(organisation=organisation)

    # When
    data = OrganisationSerializerFull(instance=organisation).data

    # Then
    assert data["overage_grace_period_used"] is False


def test_organisation_serializer_full__update_overage_fields__ignored(
    organisation: Organisation,
) -> None:
    # Given
    serializer = OrganisationSerializerFull(
        instance=organisation,
        data={
            "name": organisation.name,
            "overage_charges_enabled": True,
            "overage_grace_period_used": True,
        },
    )

    # When
    serializer.is_valid(raise_exception=True)
    organisation = serializer.save()

    # Then
    data = OrganisationSerializerFull(instance=organisation).data
    assert data["overage_charges_enabled"] is False
    assert data["overage_grace_period_used"] is False


def test_update_subscription_serializer__create__updates_subscription(
    organisation: Organisation,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ENABLE_CHARGEBEE = True
    subscription_data = {
        "subscription_id": "new-sub-id",
        "plan": "startup-v2",
        "max_seats": 10,
        "max_api_calls": 1000000,
        "customer_id": "cust-123",
        "payment_method": "CHARGEBEE",
    }
    mocker.patch(
        "organisations.serializers.get_subscription_data_from_hosted_page",
        return_value=subscription_data,
    )

    serializer = UpdateSubscriptionSerializer(
        data={"hosted_page_id": "hp-123"},
        context={"organisation": organisation.id},
    )
    serializer.is_valid(raise_exception=True)

    # When
    result = serializer.save()

    # Then
    assert result == organisation
    organisation.subscription.refresh_from_db()
    assert organisation.subscription.subscription_id == "new-sub-id"
    assert organisation.subscription.plan == "startup-v2"
