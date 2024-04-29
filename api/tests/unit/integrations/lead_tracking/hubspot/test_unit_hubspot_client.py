import pytest
from pytest_mock import MockerFixture

from integrations.lead_tracking.hubspot.client import HubspotClient
from tests.unit.integrations.lead_tracking.hubspot._hubspot_responses import (
    generate_create_company_response,
    generate_get_company_by_domain_response,
    generate_get_company_by_domain_response_no_results,
)


@pytest.fixture()
def hubspot_client(mocker: MockerFixture) -> HubspotClient:
    return HubspotClient(client=mocker.MagicMock())


def test_get_company_by_domain(hubspot_client: HubspotClient) -> None:
    # Given
    name = "Flagsmith"
    domain = "flagsmith.com"

    hubspot_response = generate_get_company_by_domain_response(name, domain)

    hubspot_client.client.crm.companies.search_api.do_search.return_value = (
        hubspot_response
    )

    # When
    company = hubspot_client.get_company_by_domain(domain)

    # Then
    assert company == hubspot_response.data["results"][0]

    hubspot_client.client.crm.companies.search_api.do_search.assert_called_once()
    call_args = hubspot_client.client.crm.companies.search_api.do_search.call_args
    assert len(call_args.kwargs["public_object_search_request"].filter_groups) == 1

    applied_filters = call_args.kwargs["public_object_search_request"].filter_groups[0][
        "filters"
    ]
    assert len(applied_filters) == 1
    assert applied_filters[0]["propertyName"] == "domain"
    assert applied_filters[0]["value"] == domain
    assert applied_filters[0]["operator"] == "EQ"


def test_get_company_by_domain_no_results(hubspot_client: HubspotClient) -> None:
    # Given
    hubspot_response = generate_get_company_by_domain_response_no_results()

    hubspot_client.client.crm.companies.search_api.do_search.return_value = (
        hubspot_response
    )

    # When
    company = hubspot_client.get_company_by_domain("foo.com")

    # Then
    assert company is None


def test_create_company_without_organisation_information(
    hubspot_client: HubspotClient,
) -> None:
    # Given
    name = "Flagsmith"
    domain = "flagsmith.com"

    hubspot_response = generate_create_company_response(name=name, domain=domain)
    hubspot_client.client.crm.companies.basic_api.create.return_value = hubspot_response

    # When
    company = hubspot_client.create_company(name=name, domain=domain)

    # Then
    assert company == hubspot_response.data

    hubspot_client.client.crm.companies.basic_api.create.assert_called_once()
    call_args = hubspot_client.client.crm.companies.basic_api.create.call_args
    assert call_args.kwargs["simple_public_object_input_for_create"].properties == {
        "active_subscription": None,
        "domain": domain,
        "name": name,
        "orgid": -1,
    }
