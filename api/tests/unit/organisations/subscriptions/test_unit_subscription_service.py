from django.conf import settings

from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.subscriptions.constants import (
    CHARGEBEE,
    MAX_API_CALLS_IN_FREE_PLAN,
    MAX_SEATS_IN_FREE_PLAN,
    XERO,
)
from organisations.subscriptions.subscription_service import (
    get_subscription_metadata,
)


def test_get_subscription_metadata_returns_default_values_if_org_does_not_have_subscription(
    organisation,
):
    # When
    subscription_metadata = get_subscription_metadata(organisation)

    # Then
    assert subscription_metadata.api_calls == MAX_API_CALLS_IN_FREE_PLAN
    assert subscription_metadata.seats == MAX_SEATS_IN_FREE_PLAN
    assert subscription_metadata.projects == settings.MAX_PROJECTS_IN_FREE_PLAN
    assert subscription_metadata.payment_source is None


def test_get_subscription_metadata_uses_chargebee_data_if_chargebee_subscription_exists(
    organisation, chargebee_subscription, mocker
):
    # Given
    seats = 10
    projects = 20
    api_calls = 30
    mocked_get_chargebee_subscription_metadata = mocker.patch(
        "organisations.subscriptions.subscription_service.get_subscription_metadata_from_id",
        autospec=True,
        return_value=ChargebeeObjMetadata(
            seats=seats, projects=projects, api_calls=api_calls
        ),
    )
    # When
    subscription_metadata = get_subscription_metadata(organisation)

    # Then
    assert subscription_metadata.api_calls == api_calls
    assert subscription_metadata.seats == seats
    assert subscription_metadata.projects == projects
    mocked_get_chargebee_subscription_metadata.assert_called_once_with(
        chargebee_subscription.subscription_id
    )
    assert subscription_metadata.payment_source == CHARGEBEE


def test_get_subscription_metadata_uses_metadata_from_subscription_for_non_chargebee_subscription(
    organisation, xero_subscription
):
    # When
    subscription_metadata = get_subscription_metadata(organisation)

    # Then
    assert subscription_metadata.api_calls == xero_subscription.max_api_calls
    assert subscription_metadata.seats == xero_subscription.max_seats
    assert subscription_metadata.projects is None
    assert subscription_metadata.payment_source == XERO
