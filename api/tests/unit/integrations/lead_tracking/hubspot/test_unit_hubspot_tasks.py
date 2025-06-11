import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from users.models import FFAdminUser
from integrations.lead_tracking.hubspot.tasks import (
    track_hubspot_organisation_lead,
    track_hubspot_user_contact,
)


def test_track_hubspot_user_contact_skips_when_tracking_disabled(
    settings: SettingsWrapper,
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = False

    # When / Then
    with pytest.raises(AssertionError):
        track_hubspot_user_contact(user_id=admin_user.id)


def test_track_hubspot_user_contact_skips_when_should_track_false(
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
    track_hubspot_user_contact(user_id=admin_user.id)

    # Then
    mock_create_contact.assert_not_called()


def test_track_hubspot_organisation_lead_skips_when_tracking_disabled(
    settings: SettingsWrapper,
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = False

    # When / Then
    with pytest.raises(AssertionError):
        track_hubspot_organisation_lead(user_id=admin_user.id, organisation_id=1)


def test_track_hubspot_organisation_lead_skips_when_should_track_false(
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
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker.create_organisation_lead"
    )

    # When
    track_hubspot_organisation_lead(user_id=admin_user.id, organisation_id=1)

    # Then
    mock_create_lead.assert_not_called()
