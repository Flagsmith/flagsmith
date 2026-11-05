import json
import typing

import pytest
import responses
import urllib3
from hubspot.conversations.visitor_identification import (  # type: ignore[import-untyped]
    ApiException,
)
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from rest_framework import status

from integrations.lead_tracking.hubspot.client import HubspotClient
from integrations.lead_tracking.hubspot.constants import (
    HUBSPOT_FORM_ID_SAAS,
    HUBSPOT_PORTAL_ID,
    HUBSPOT_ROOT_FORM_URL,
    HUBSPOT_VISITOR_IDENTIFICATION_TIMEOUT_SECONDS,
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
@pytest.mark.parametrize(
    "hubspot_cookie_body,expected_context",
    [
        (
            "test_hubspot_cookie",
            {
                "hutk": "test_hubspot_cookie",
                "pageUri": "www.flagsmith.com",
                "pageName": "Homepage",
            },
        ),
        (None, {}),
    ],
)
def test_create_lead_form__valid_user_data__submits_form_successfully(
    staff_user: FFAdminUser,
    hubspot_client: HubspotClient,
    hubspot_cookie_body: str | None,
    expected_context: dict[str, str],
) -> None:
    # Given
    url = f"{HUBSPOT_ROOT_FORM_URL}/{HUBSPOT_PORTAL_ID}/{HUBSPOT_FORM_ID_SAAS}"
    responses.add(
        method="POST",
        url=url,
        status=status.HTTP_200_OK,
        json={"inlineMessage": "Thanks for submitting the form."},
    )
    utms_data = {
        "utm_source": "test_source",
        "utm_medium": "test_medium",
        "utm_campaign": "test_campaign",
        "utm_content": "test_content",
        "utm_term": "test_term",
    }
    # When
    response = hubspot_client.create_lead_form(
        staff_user, hubspot_cookie_body, utms_data
    )

    # Then
    assert len(responses.calls) == 1
    assert response == {"inlineMessage": "Thanks for submitting the form."}
    call: responses.Call = responses.calls[0]  # type: ignore[assignment]
    request_body = json.loads(call.request.body)
    assert response == {"inlineMessage": "Thanks for submitting the form."}

    fields: list[dict[str, str]] = request_body["fields"]

    assert {"objectTypeId": "0-1", "name": "email", "value": staff_user.email} in fields
    assert {
        "objectTypeId": "0-1",
        "name": "firstname",
        "value": staff_user.first_name,
    } in fields
    assert {
        "objectTypeId": "0-1",
        "name": "lastname",
        "value": staff_user.last_name,
    } in fields

    # Test UTMs
    assert {
        "objectTypeId": "0-1",
        "name": "utm_source",
        "value": "test_source",
    } in fields
    assert {
        "objectTypeId": "0-1",
        "name": "utm_medium",
        "value": "test_medium",
    } in fields
    assert {
        "objectTypeId": "0-1",
        "name": "utm_campaign",
        "value": "test_campaign",
    } in fields
    assert {
        "objectTypeId": "0-1",
        "name": "utm_content",
        "value": "test_content",
    } in fields
    assert {"objectTypeId": "0-1", "name": "utm_term", "value": "test_term"} in fields

    context = request_body.get("context", {})
    assert context == expected_context


@responses.activate
def test_create_lead_form__api_returns_error__logs_error(
    staff_user: FFAdminUser,
    hubspot_client: HubspotClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given
    hubspot_cookie = "test_hubspot_cookie"
    url = f"{HUBSPOT_ROOT_FORM_URL}/{HUBSPOT_PORTAL_ID}/{HUBSPOT_FORM_ID_SAAS}"
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
    assert caplog.messages == [
        "Creating Hubspot lead form for user staff@example.com with hubspot cookie test_hubspot_cookie",
        "Problem posting data to Hubspot's form API due to 400 status code and following response: "
        + '{"error": "Problem processing."}',
    ]


def test_get_company_by_domain__company_exists__returns_company(
    hubspot_client: HubspotClient,
) -> None:
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


def test_get_company_by_domain__no_results__returns_none(
    hubspot_client: HubspotClient,
) -> None:
    # Given
    hubspot_response = generate_get_company_by_domain_response_no_results()

    hubspot_client.client.crm.companies.search_api.do_search.return_value = (
        hubspot_response
    )

    # When
    company = hubspot_client.get_company_by_domain("foo.com")

    # Then
    assert company is None


def test_create_company__without_organisation_info__creates_with_name_and_domain(
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


@pytest.mark.parametrize(
    "kwargs, expected_properties",
    [
        (
            {"name": "Test Organisation", "flagsmith_organisation_id": 1},
            {"name": "Test Organisation", "orgid_unique": "1"},
        ),
        (
            {
                "name": "Test Organisation",
                "active_subscription": "scaleup",
                "flagsmith_organisation_id": 1,
            },
            {
                "name": "Test Organisation",
                "active_subscription": "scaleup",
                "orgid_unique": "1",
            },
        ),
        (
            {"active_subscription": "scaleup", "flagsmith_organisation_id": 1},
            {"active_subscription": "scaleup", "orgid_unique": "1"},
        ),
        (
            {
                "name": None,
                "active_subscription": None,
                "flagsmith_organisation_id": None,
            },
            {},
        ),
    ],
)
def test_update_company__with_properties__calls_hubspot_api_with_expected_properties(
    hubspot_client: HubspotClient,
    kwargs: dict[str, typing.Any],
    expected_properties: dict[str, typing.Any],
) -> None:
    # Given / When
    mock_update_company = hubspot_client.client.crm.companies.basic_api.update

    hubspot_client.update_company(hubspot_company_id="123", **kwargs)

    # Then
    mock_update_company.assert_called_once()
    _, call_kwargs = mock_update_company.call_args
    assert call_kwargs["company_id"] == "123"

    simple_input = call_kwargs["simple_public_object_input"]
    assert simple_input.properties == expected_properties


@pytest.mark.parametrize(
    "first_name, last_name, expected_first_name, expected_last_name",
    [
        ("Ada", "Lovelace", "Ada", "Lovelace"),
        ("", "", None, None),
    ],
)
def test_create_visitor_identification_token__hubspot_returns_token__returns_token(
    db: None,
    hubspot_client: HubspotClient,
    first_name: str,
    last_name: str,
    expected_first_name: str | None,
    expected_last_name: str | None,
) -> None:
    # Given
    user = FFAdminUser.objects.create(
        email="chat@example.com", first_name=first_name, last_name=last_name
    )
    mock_generate_token = hubspot_client.client.conversations.visitor_identification.generate_api.generate_token
    mock_generate_token.return_value.token = "test-token"

    # When
    token = hubspot_client.create_visitor_identification_token(user)

    # Then
    assert token == "test-token"
    mock_generate_token.assert_called_once()
    _, call_kwargs = mock_generate_token.call_args
    request = call_kwargs["identification_token_generation_request"]
    assert request.email == "chat@example.com"
    assert request.first_name == expected_first_name
    assert request.last_name == expected_last_name
    assert (
        call_kwargs["_request_timeout"]
        == HUBSPOT_VISITOR_IDENTIFICATION_TIMEOUT_SECONDS
    )


@pytest.mark.parametrize(
    "error",
    [
        ApiException(status=403, reason="Forbidden"),
        urllib3.exceptions.ReadTimeoutError(None, "", "Read timed out."),  # type: ignore[arg-type]
    ],
)
def test_create_visitor_identification_token__hubspot_fails__logs_and_returns_none(
    staff_user: FFAdminUser,
    hubspot_client: HubspotClient,
    log: StructuredLogCapture,
    error: Exception,
) -> None:
    # Given
    hubspot_client.client.conversations.visitor_identification.generate_api.generate_token.side_effect = error

    # When
    token = hubspot_client.create_visitor_identification_token(staff_user)

    # Then
    assert token is None
    assert log.events == [
        {
            "event": "visitor_identification_token.create_failed",
            "level": "error",
            "user__id": staff_user.id,
            "exc_info": True,
        }
    ]
