import pytest

from integrations.lead_tracking.pipedrive.exceptions import (
    MultipleMatchingOrganizationsError,
)
from integrations.lead_tracking.pipedrive.lead_tracker import (
    PipedriveLeadTracker,
)
from integrations.lead_tracking.pipedrive.models import PipedriveOrganization
from users.models import FFAdminUser


def test_create_lead_adds_to_existing_organization_if_exists(db, mocker):
    # Given
    user = FFAdminUser(email="elmerfudd@looneytunes.com")

    organization = PipedriveOrganization(name="some-org", id=1)
    mock_pipedrive_client = mocker.MagicMock()
    mock_pipedrive_client.search_organizations.return_value = [organization]

    lead_tracker = PipedriveLeadTracker(client=mock_pipedrive_client)

    # When
    lead_tracker.create_lead(user)

    # Then
    mock_pipedrive_client.create_lead.assert_called_once_with(
        title=user.email, organization_id=organization.id
    )


def test_create_lead_creates_new_organization_if_not_exists(db, settings, mocker):
    # Given
    domain_organization_field_key = "domain-organization-field-key"
    settings.PIPEDRIVE_DOMAIN_ORGANIZATION_FIELD_KEY = domain_organization_field_key

    user = FFAdminUser(email="elmerfudd@looneytunes.com")

    organization = PipedriveOrganization(name="some-org", id=1)
    mock_pipedrive_client = mocker.MagicMock()
    mock_pipedrive_client.search_organizations.return_value = []
    mock_pipedrive_client.create_organization.return_value = organization

    lead_tracker = PipedriveLeadTracker(client=mock_pipedrive_client)

    # When
    lead_tracker.create_lead(user)

    # Then
    mock_pipedrive_client.create_lead.assert_called_once_with(
        title=user.email, organization_id=organization.id
    )
    mock_pipedrive_client.create_organization.assert_called_once_with(
        name="looneytunes",
        organization_fields={domain_organization_field_key: "looneytunes.com"},
    )


def test_create_lead_throws_exception_if_multiple_organisations_found(
    db, settings, mocker
):
    # Given
    user = FFAdminUser(email="elmerfudd@looneytunes.com")

    organization_1 = PipedriveOrganization(name="some-org-1", id=1)
    organization_2 = PipedriveOrganization(name="some-org-2", id=2)
    mock_pipedrive_client = mocker.MagicMock()
    mock_pipedrive_client.search_organizations.return_value = [
        organization_1,
        organization_2,
    ]

    lead_tracker = PipedriveLeadTracker(client=mock_pipedrive_client)

    # When
    with pytest.raises(MultipleMatchingOrganizationsError):
        lead_tracker.create_lead(user)

    # Then
    mock_pipedrive_client.create_lead.assert_not_called()
