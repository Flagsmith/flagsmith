import logging

import pytest
import responses
from pytest_mock import MockerFixture
from rest_framework import status

from integrations.lead_tracking.hubspot.client import HubspotClient
from integrations.lead_tracking.hubspot.constants import (
    HUBSPOT_FORM_ID,
    HUBSPOT_PORTAL_ID,
    HUBSPOT_ROOT_FORM_URL,
)
from tests.unit.integrations.lead_tracking.hubspot._hubspot_responses import (
    generate_create_company_response,
    generate_get_company_by_domain_response,
    generate_get_company_by_domain_response_no_results,
)
from users.models import FFAdminUser


@pytest.fixture()
def hubspot_client(mocker: MockerFixture) -> HubspotClient:
    return HubspotClient(client=mocker.MagicMock())


@responses.activate
def test_create_lead_form(
    staff_user: FFAdminUser,
    hubspot_client: HubspotClient,
) -> None:
    # Given
    hubspot_cookie = "test_hubspot_cookie"
    url = f"{HUBSPOT_ROOT_FORM_URL}/{HUBSPOT_PORTAL_ID}/{HUBSPOT_FORM_ID}"
    responses.add(
        method="POST",
        url=url,
        status=status.HTTP_200_OK,
        json={"inlineMessage": "Thanks for submitting the form."},
    )

    # When
    response = hubspot_client.create_lead_form(staff_user, hubspot_cookie)

    # Then
    assert response == {"inlineMessage": "Thanks for submitting the form."}


@responses.activate
def test_create_lead_form_error(
    staff_user: FFAdminUser,
    hubspot_client: HubspotClient,
    inspecting_handler: logging.Handler,
) -> None:
    # Given
    from integrations.lead_tracking.hubspot.client import logger

    logger.addHandler(inspecting_handler)

    hubspot_cookie = "test_hubspot_cookie"
    url = f"{HUBSPOT_ROOT_FORM_URL}/{HUBSPOT_PORTAL_ID}/{HUBSPOT_FORM_ID}"
    responses.add(
        method="POST",
        url=url,
        status=status.HTTP_400_BAD_REQUEST,
        json={"error": "Problem processing."},
    )

    # When
    response = hubspot_client.create_lead_form(staff_user, hubspot_cookie)

    # Then
    assert response == {"error": "Problem processing."}
    assert inspecting_handler.messages == [
        "Problem posting data to Hubspot's form API due to 400 status code and following form data "
        + '{"error": "Problem processing."}'
    ]


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
        "domain": domain,
        "name": name,
    }
