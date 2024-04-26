from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from integrations.lead_tracking.hubspot.client import HubspotClient
from integrations.lead_tracking.hubspot.tasks import (
    track_hubspot_lead_without_organisation,
)
from users.models import FFAdminUser, HubspotLead


def test_track_hubspot_lead_without_organisation_does_nothing_if_lead_exists(
    db: None, mocker: MockerFixture, settings: SettingsWrapper
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True

    user = FFAdminUser.objects.create(email="test@example.com")
    HubspotLead.objects.create(user=user, hubspot_id="foo")

    mock_hubspot_client = mocker.MagicMock(spec=HubspotClient)
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotClient",
        return_value=mock_hubspot_client,
    )

    # When
    track_hubspot_lead_without_organisation(user_id=user.id)

    # Then
    mock_hubspot_client.create_contact.assert_not_called()


def test_track_hubspot_lead_without_organisation(
    db: None, mocker: MockerFixture, settings: SettingsWrapper
) -> None:
    # Given
    hubspot_company_id = "company-id"
    hubspot_contact_id = "contact-id"

    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True

    user = FFAdminUser.objects.create(email="test@example.com")

    mock_hubspot_client = mocker.MagicMock(spec=HubspotClient)
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotClient",
        return_value=mock_hubspot_client,
    )

    mock_hubspot_client.get_contact.return_value = None
    mock_hubspot_client.get_company_by_domain.return_value = None
    mock_hubspot_client.create_company.return_value = {"id": hubspot_company_id}
    mock_hubspot_client.create_contact.return_value = {"id": hubspot_contact_id}

    # When
    track_hubspot_lead_without_organisation(user_id=user.id)

    # Then
    mock_hubspot_client.create_contact.assert_called_once_with(user, hubspot_company_id)
    assert HubspotLead.objects.filter(user=user).exists()
