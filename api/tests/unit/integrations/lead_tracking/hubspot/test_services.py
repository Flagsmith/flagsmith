from pytest_mock import MockerFixture

from integrations.lead_tracking.hubspot.constants import (
    HUBSPOT_ACTIVE_SUBSCRIPTION_SELF_HOSTED,
)
from integrations.lead_tracking.hubspot.services import (
    create_self_hosted_onboarding_lead,
)


def test_create_self_hosted_onboarding_lead_with_existing_company(
    mocker: MockerFixture,
) -> None:
    # Given
    mocked_hubspot_client = mocker.patch(
        "integrations.lead_tracking.hubspot.services.HubspotClient", autospec=True
    )
    email = "user@flagsmith.com"
    organisation_name = "Flagsmith"
    first_name = "user"
    last_name = "test"

    company_domain = "flagsmith.com"
    company_id = "111"

    mocked_hubspot_client().get_company_by_domain.return_value = {"id": company_id}

    # When
    create_self_hosted_onboarding_lead(email, first_name, last_name, organisation_name)

    # Then
    mocked_hubspot_client().get_company_by_domain.assert_called_once_with(
        company_domain
    )

    mocked_hubspot_client().create_company.assert_not_called()

    mocked_hubspot_client().create_self_hosted_contact.assert_called_once_with(
        email, first_name, last_name, company_id
    )


def test_create_self_hosted_onboarding_lead_with_new_company(
    mocker: MockerFixture,
) -> None:
    # Given
    mocked_hubspot_client = mocker.patch(
        "integrations.lead_tracking.hubspot.services.HubspotClient", autospec=True
    )
    email = "user@flagsmith.com"
    organisation_name = "Flagsmith"
    first_name = "user"
    last_name = "test"

    company_domain = "flagsmith.com"
    company_id = "111"

    mocked_hubspot_client().get_company_by_domain.return_value = None
    mocked_hubspot_client().create_company.return_value = {"id": company_id}

    # When
    create_self_hosted_onboarding_lead(email, first_name, last_name, organisation_name)

    # Then
    mocked_hubspot_client().get_company_by_domain.assert_called_once_with(
        company_domain
    )

    mocked_hubspot_client().create_company.assert_called_once_with(
        name=organisation_name,
        domain=company_domain,
        active_subscription=HUBSPOT_ACTIVE_SUBSCRIPTION_SELF_HOSTED,
    )

    mocked_hubspot_client().create_self_hosted_contact.assert_called_once_with(
        email, first_name, last_name, company_id
    )
