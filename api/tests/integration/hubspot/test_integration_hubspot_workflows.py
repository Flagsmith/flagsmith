import json
from typing import NamedTuple
from unittest.mock import MagicMock

import pytest
from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from integrations.lead_tracking.hubspot.lead_tracker import HubspotLeadTracker


@pytest.fixture()
def hubspot_access_token() -> str:
    return "foobar"


@pytest.fixture(autouse=True)
def enable_hubspot(settings: SettingsWrapper, hubspot_access_token: str) -> None:
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    settings.HUBSPOT_ACCESS_TOKEN = hubspot_access_token


@pytest.fixture()
def mocked_hubspot_lead_tracker(mocker: MockerFixture) -> MagicMock:
    _mocked_hubspot_lead_tracker = mocker.MagicMock(spec=HubspotLeadTracker)
    mocker.patch(
        "api.integrations.lead_tracking.hubspot.tasks.HubspotLeadTracker",
        return_value=_mocked_hubspot_lead_tracker,
    )
    return _mocked_hubspot_lead_tracker


class UserDetails(NamedTuple):
    email: str
    first_name: str
    last_name: str


@pytest.fixture()
def user_details() -> UserDetails:
    return UserDetails(
        email="john.doe@example.com",
        first_name="John",
        last_name="Doe",
    )


@pytest.fixture()
def registered_user_api_client(
    api_client: APIClient,
    user_details: UserDetails,
) -> APIClient:
    url = reverse("api-v1:custom_auth:ffadminuser-list")
    data = {
        "email": user_details.email,
        "first_name": user_details.first_name,
        "last_name": user_details.last_name,
    }
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_201_CREATED

    # TODO: use some kind of request capture fixture to verify that
    #  the correct form (and only the form) was sent to hubspot

    api_client.credentials(HTTP_AUTHORIZATION=f"Token {response.json()['token']}")
    return api_client


@pytest.fixture()
def email_invite(
    admin_client: APIClient, organisation: int, user_details: UserDetails
) -> str:
    url = reverse("api-v1:organisations:organisation-invite", args=[organisation])
    data = {"invites": [{"email": user_details.email}]}
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    return response.json()["hash"]


@pytest.fixture()
def invite_link(admin_client: APIClient, organisation: int) -> str:
    url = reverse(
        "api-v1:organisations:organisation-invite-links-list",
        args=[organisation],
    )
    response = admin_client.post(url)
    return response.json()["hash"]


def test_correct_hubspot_calls_made_when_user_registers_and_joins_organisation_via_email_invite(
    registered_user_api_client: APIClient,
    email_invite: str,
) -> None:
    # Given
    assert email_invite

    # Now, let's join the organisation
    join_organisation_url = reverse(
        "api-v1:users:user-join-organisation", args=[email_invite]
    )
    response = registered_user_api_client.post(join_organisation_url)
    assert response.status_code == status.HTTP_200_OK

    # TODO: verify that the correct call is made to hubspot to update the
    #  contact's company


def test_correct_hubspot_calls_made_when_user_registers_and_joins_organisation_via_invite_link(
    registered_user_api_client: APIClient,
    invite_link: str,
) -> None:
    # Given
    assert invite_link

    # Now, let's join the organisation
    join_organisation_url = reverse(
        "api-v1:users:user-join-organisation", args=[invite_link]
    )
    response = registered_user_api_client.post(join_organisation_url)
    assert response.status_code == status.HTTP_200_OK

    # TODO: verify that the correct call is made to hubspot to update the
    #  contact's company


def test_company_is_updated_when_user_creates_organisation(
    registered_user_api_client: APIClient,
) -> None:
    create_organisation_url = reverse("api-v1:organisations:organisation-list")
    data = {"name": "test organisation"}

    response = registered_user_api_client.post(create_organisation_url, data=data)
    assert response.status_code == status.HTTP_201_CREATED

    # TODO: verify that the correct call is made to hubspot to update the
    #  contact's company
