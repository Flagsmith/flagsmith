import json
from typing import NamedTuple
from unittest.mock import MagicMock
from django.test import Client
import pytest
from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient
from users.models import FFAdminUser
from integrations.lead_tracking.hubspot.tasks import track_hubspot_user_contact
from integrations.lead_tracking.hubspot.lead_tracker import HubspotLeadTracker
from task_processor.task_run_method import TaskRunMethod
from integrations.lead_tracking.hubspot.client import HubspotClient
from users.models import HubspotTracker


@pytest.fixture()
def hubspot_access_token() -> str:
    return "foobar"


@pytest.fixture(autouse=True)
def enable_hubspot(settings: SettingsWrapper, hubspot_access_token: str) -> None:
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    settings.HUBSPOT_ACCESS_TOKEN = hubspot_access_token
    settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY


@pytest.fixture()
def mocked_hubspot_lead_tracker(mocker: MockerFixture) -> MagicMock:
    _mocked_hubspot_lead_tracker: MagicMock = mocker.MagicMock(spec=HubspotLeadTracker)
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker",
        return_value=_mocked_hubspot_lead_tracker,
    )
    return _mocked_hubspot_lead_tracker


@pytest.fixture()
def mock_hubspot_client(request):  # type: ignore[no-untyped-def]
    return request.getfixturevalue(request.param)


# TODO: Fix circular imports to allow mocking on the fly
@pytest.fixture()
def mock_client_no_contact(mocker: MockerFixture) -> MagicMock:
    mock_client: MagicMock = mocker.MagicMock()
    mock_client.get_contact.return_value = None
    mock_client.create_contact.return_value = {"id": "123"}
    mock_client.create_lead_form.return_value = None

    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker._get_client",
        return_value=mock_client,
    )
    return mock_client


@pytest.fixture()
def mock_client_existing_contact(mocker: MockerFixture) -> MagicMock:
    mock_client: MagicMock = mocker.MagicMock()
    mock_client.get_contact.return_value = {"id": "123"}
    mock_client.create_contact.return_value = {"id": "123"}
    mock_client.create_lead_form.return_value = None

    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker._get_client",
        return_value=mock_client,
    )
    return mock_client


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
    hash: str = response.json()["hash"]
    return hash


@pytest.fixture()
def invite_link(admin_client: APIClient, organisation: int) -> str:
    url = reverse(
        "api-v1:organisations:organisation-invite-links-list",
        args=[organisation],
    )
    response = admin_client.post(url)
    hash: str = response.json()["hash"]
    return hash


def test_correct_hubspot_calls_made_when_user_registers_and_joins_organisation_via_email_invite(
    # db: None,
    # registered_user_api_client: APIClient,
    # email_invite: str,
) -> None:
    pass


#     # Given
#     assert email_invite

#     # Now, let's join the organisation
#     join_organisation_url = reverse(
#         "api-v1:users:user-join-organisation", args=[email_invite]
#     )
#     response = registered_user_api_client.post(join_organisation_url)
#     assert response.status_code == status.HTTP_200_OK

#     # TODO: verify that the correct call is made to hubspot to update the
#     #  contact's company


def test_correct_hubspot_calls_made_when_user_registers_and_joins_organisation_via_invite_link(
    # db: None,
    # registered_user_api_client: APIClient,
    # invite_link: str,
) -> None:
    pass


#     # Given
#     assert invite_link

#     # Now, let's join the organisation
#     join_organisation_url = reverse(
#         "api-v1:users:user-join-organisation", args=[invite_link]
#     )
#     response = registered_user_api_client.post(join_organisation_url)
#     assert response.status_code == status.HTTP_200_OK

#     # TODO: verify that the correct call is made to hubspot to update the
#     #  contact's company


def test_company_is_updated_when_user_creates_organisation(
    db: None,
    # registered_user_api_client: APIClient,
) -> None:
    pass


#     create_organisation_url = reverse("api-v1:organisations:organisation-list")
#     data = {"name": "test organisation"}

#     response = registered_user_api_client.post(create_organisation_url, data=data)
#     assert response.status_code == status.HTTP_201_CREATED

#     # TODO: verify that the correct call is made to hubspot to update the
#     #  contact's company


def test_user_signup_triggers_hubspot_create_contact_creation(
    db: None,
    client: Client,
    mocker: MockerFixture,
    enable_hubspot: None,
    mocked_hubspot_lead_tracker: MagicMock,
) -> None:
    # Given
    password = FFAdminUser.objects.make_random_password()
    sign_up_type = "NO_INVITE"

    mock_track_hubspot_user_contact = mocker.patch(
        "users.models.track_hubspot_user_contact"
    )
    mock_track_hubspot_user_contact.delay = mocker.MagicMock()

    email = "test@example.com"
    register_data = {
        "email": email,
        "password": password,
        "re_password": password,
        "first_name": "test",
        "last_name": "tester",
        "sign_up_type": sign_up_type,
    }

    # When
    response = client.post(
        reverse("api-v1:custom_auth:ffadminuser-list"),
        data=json.dumps(register_data),
        content_type="application/json",
    )

    # Then
    created_user = FFAdminUser.objects.filter(
        email=email, sign_up_type=sign_up_type
    ).first()
    assert created_user
    assert response.status_code == status.HTTP_201_CREATED
    mock_track_hubspot_user_contact.delay.assert_called_once_with(
        args=(created_user.id,),
    )


@pytest.mark.parametrize(
    "mock_hubspot_client",
    [
        "mock_client_no_contact",
        "mock_client_existing_contact",
    ],
    indirect=["mock_hubspot_client"],
)
def test_create_lead_form_is_sent_to_hubspot_for_all_user_signing_up(
    db: None,
    client: Client,
    mocker: MockerFixture,
    # mocked_hubspot_lead_tracker: MagicMock,
    mock_hubspot_client: MagicMock,
    settings: SettingsWrapper,
) -> None:
    # Given
    user = FFAdminUser.objects.create_user(
        email="test@example.com",
        sign_up_type="NO_INVITE",
    )  # type: ignore[no-untyped-call]
    HubspotTracker.objects.update_or_create(
        user=user,
        defaults={"hubspot_cookie": "abc123"},
    )

    # mocker.spy(HubspotLeadTracker, "create_lead")
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    settings.HUBSPOT_ACCESS_TOKEN = hubspot_access_token
    settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY

    track_hubspot_user_contact(user.id)

    mock_hubspot_client.create_lead_form.assert_called_once_with(
        user=user, hubspot_cookie="abc123"
    )


def test_user_is_updated_in_hubspot_if_already_exists_when_signing_up(
    api_client: APIClient,
    user_details: UserDetails,
) -> None:
    pass


def test_organisation_is_created_via_domain_if_user_did_not_join_an_organisation(
    api_client: APIClient,
    user_details: UserDetails,
) -> None:
    pass


def test_create_new_organisation_and_add_user_as_contact_if_new_organisation_is_created(
    api_client: APIClient,
    user_details: UserDetails,
) -> None:
    pass
