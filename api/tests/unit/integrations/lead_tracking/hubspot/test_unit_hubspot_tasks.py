import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from integrations.lead_tracking.hubspot.tasks import (
    create_hubspot_contact_for_user,
    track_hubspot_lead_v2,
    update_hubspot_active_subscription,
)
from organisations.models import Organisation
from users.models import FFAdminUser


def test_create_hubspot_contact_for_user__tracking_disabled__raises_assertion_error(
    settings: SettingsWrapper,
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = False

    # When / Then
    with pytest.raises(AssertionError):
        create_hubspot_contact_for_user(user_id=admin_user.id)


def test_create_hubspot_contact_for_user__should_track_false__does_not_create_contact(
    settings: SettingsWrapper,
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker.should_track",
        return_value=False,
    )
    mock_create_contact = mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker.create_user_hubspot_contact"
    )

    # When
    create_hubspot_contact_for_user(user_id=admin_user.id)

    # Then
    mock_create_contact.assert_not_called()


def test_track_hubspot_lead__tracking_disabled__raises_assertion_error(
    settings: SettingsWrapper,
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = False

    # When / Then
    with pytest.raises(AssertionError):
        track_hubspot_lead_v2(user_id=admin_user.id, organisation_id=1)


def test_track_hubspot_lead__should_track_false__does_not_create_lead(
    settings: SettingsWrapper,
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker.should_track",
        return_value=False,
    )
    mock_create_lead = mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker.create_lead"
    )

    # When
    track_hubspot_lead_v2(user_id=admin_user.id, organisation_id=1)

    # Then
    mock_create_lead.assert_not_called()


def test_update_hubspot_active_subscription__tracking_disabled__raises_assertion_error(
    settings: SettingsWrapper,
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = False

    # When / Then
    with pytest.raises(AssertionError):
        update_hubspot_active_subscription(subscription_id=1)


def test_update_hubspot_active_subscription__tracking_enabled__calls_update(
    db: None,
    settings: SettingsWrapper,
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True

    mock_update_company_active_subscription = mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker.update_company_active_subscription"
    )

    # When
    update_hubspot_active_subscription(organisation.subscription.id)

    # Then
    mock_update_company_active_subscription.assert_called_once_with(
        organisation.subscription
    )
