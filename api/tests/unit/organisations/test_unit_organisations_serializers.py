from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from organisations.models import Organisation
from organisations.serializers import (
    OrganisationSerializerFull,
    UpdateSubscriptionSerializer,
)


def test_organisation_serializer_full__onboarding_org__serialises_onboarding_variant(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    get_onboarding_variant_mock = mocker.patch(
        "organisations.serializers.get_onboarding_variant",
        return_value="single_page",
        autospec=True,
    )

    # When
    data = OrganisationSerializerFull(instance=organisation).data

    # Then
    assert data["onboarding_variant"] == "single_page"
    get_onboarding_variant_mock.assert_called_once_with(organisation)


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
