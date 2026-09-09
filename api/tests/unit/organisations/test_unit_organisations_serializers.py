from datetime import timedelta

from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from organisations.models import (
    Organisation,
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


def test_organisation_serializer_full__restriction_enabled__reports_both_fields(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("api_limiting_stop_serving_flags")
    organisation.stop_serving_flags = True
    organisation.save()

    # When
    data = OrganisationSerializerFull(instance=organisation).data

    # Then
    assert data["stop_serving_flags"] is True
    assert data["api_limit_restriction_enabled"] is True


def test_organisation_serializer_full__restriction_disabled__reports_both_fields(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features()

    # When
    data = OrganisationSerializerFull(instance=organisation).data

    # Then
    assert data["stop_serving_flags"] is False
    assert data["api_limit_restriction_enabled"] is False


# The row a restricted organisation carries says nothing about its overages.
def test_organisation_serializer_full__monthly_paid_plan__reports_overage_charges(
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
    organisation.subscription.save()

    # When
    data = OrganisationSerializerFull(instance=organisation).data

    # Then
    assert data["overage_charges_enabled"] is True


def test_organisation_serializer_full__update_restriction_fields__ignored(
    organisation: Organisation,
) -> None:
    # Given
    serializer = OrganisationSerializerFull(
        instance=organisation,
        data={
            "name": organisation.name,
            "stop_serving_flags": True,
            "block_access_to_admin": True,
        },
    )

    # When
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # Then
    organisation.refresh_from_db()
    assert organisation.stop_serving_flags is False
    assert organisation.block_access_to_admin is False


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
