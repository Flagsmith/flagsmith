from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from onboarding.views import SEND_SUPPORT_REQUEST_URL
from organisations.models import Organisation
from users.models import FFAdminUser


def test__send_onboarding_request_to_saas_flagsmith_view_for_non_admin_user(
    test_user_client: APIClient,
):
    # Given
    url = reverse("api-v1:onboarding:send-onboarding-request")

    # When
    response = test_user_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test__send_onboarding_request_to_saas_flagsmith_view_without_org(
    db: None, admin_client_original: APIClient
) -> None:
    # Given
    url = reverse("api-v1:onboarding:send-onboarding-request")

    # When
    response = admin_client_original.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["error"]
        == "Please create an organisation before requesting support"
    )


def test__send_onboarding_request_to_saas_flagsmith_view(
    db: None,
    admin_client_original: APIClient,
    mocker: MockerFixture,
    organisation: Organisation,
    admin_user: FFAdminUser,
) -> None:
    # Given
    mocked_requests = mocker.patch("onboarding.views.requests")
    url = reverse("api-v1:onboarding:send-onboarding-request")

    # When
    response = admin_client_original.post(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mocked_requests.post.assert_called_once_with(
        SEND_SUPPORT_REQUEST_URL,
        data={
            "first_name": admin_user.first_name,
            "last_name": admin_user.last_name,
            "email": admin_user.email,
            "organisation_name": organisation.name,
        },
        timeout=30,
    )


def test__receive_support_request_from_self_hosted_view_without_hubspot_token(
    settings: SettingsWrapper, api_client: APIClient
):
    # Given
    settings.HUBSPOT_ACCESS_TOKEN = None
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["onboarding_request"] = "10/hour"

    url = reverse("api-v1:onboarding:receive-onboarding-request")

    # When
    response = api_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "HubSpot access token not configured"


def test__receive_support_request_from_self_hosted_view(
    settings: SettingsWrapper, api_client: APIClient, mocker: MockerFixture
):
    # Given
    settings.HUBSPOT_ACCESS_TOKEN = "some-token"
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["onboarding_request"] = "2/hour"

    mocked_create_self_hosted_onboarding_lead = mocker.patch(
        "onboarding.views.create_self_hosted_onboarding_lead"
    )

    data = {
        "organisation_name": "org-1",
        "first_name": "user",
        "last_name": "test",
        "email": "user@flagsmith.com",
    }
    url = reverse("api-v1:onboarding:receive-onboarding-request")

    # When
    response = api_client.post(url, data=data)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Then
    # Next request should be throttled
    response = api_client.post(url, data=data)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    mocked_create_self_hosted_onboarding_lead.assert_called_once_with(**data)
