from unittest.mock import MagicMock

from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from onboarding.tasks import SEND_SUPPORT_REQUEST_URL
from organisations.models import Organisation
from users.models import FFAdminUser


def test_send_onboarding_request_to_saas_flagsmith_view_for_non_admin_user(
    staff_client: APIClient, is_oss: MagicMock
) -> None:
    # Given
    url = reverse("api-v1:onboarding:send-onboarding-request")

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_send_onboarding_request_to_saas_flagsmith_view_without_org(
    admin_client_original: APIClient, is_oss: MagicMock
) -> None:
    # Given
    url = reverse("api-v1:onboarding:send-onboarding-request")

    # When
    response = admin_client_original.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["message"]
        == "Please create an organisation before requesting support"
    )


def test_send_onboarding_request_to_saas_flagsmith_view(
    admin_client_original: APIClient,
    mocker: MockerFixture,
    organisation: Organisation,
    admin_user: FFAdminUser,
    is_oss: MagicMock,
) -> None:
    # Given
    mocked_requests = mocker.patch("onboarding.tasks.requests")
    url = reverse("api-v1:onboarding:send-onboarding-request")

    # When
    response = admin_client_original.post(url, data={"hubspotutk": "test"})

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mocked_requests.post.assert_called_once_with(
        SEND_SUPPORT_REQUEST_URL,
        data={
            "first_name": admin_user.first_name,
            "last_name": admin_user.last_name,
            "email": admin_user.email,
            "hubspot_cookie": "test",
        },
        timeout=30,
    )


def test_receive_support_request_from_self_hosted_view_without_hubspot_token(
    settings: SettingsWrapper,
    api_client: APIClient,
    db: None,
    is_saas: MagicMock,
) -> None:
    # Given
    settings.HUBSPOT_ACCESS_TOKEN = None

    url = reverse("api-v1:onboarding:receive-onboarding-request")

    # When
    response = api_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["message"] == "HubSpot access token not configured"


def test_receive_support_request_from_self_hosted_view(
    settings: SettingsWrapper,
    api_client: APIClient,
    mocker: MockerFixture,
    db: None,
    is_saas: None,
) -> None:
    # Given
    settings.HUBSPOT_ACCESS_TOKEN = "some-token"

    mocked_create_self_hosted_onboarding_lead = mocker.patch(
        "integrations.lead_tracking.hubspot.services.create_self_hosted_onboarding_lead"
    )

    data = {
        "first_name": "user",
        "last_name": "test",
        "email": "user@flagsmith.com",
        "hubspot_cookie": "test",
    }
    url = reverse("api-v1:onboarding:receive-onboarding-request")

    # When
    response = api_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mocked_create_self_hosted_onboarding_lead.assert_called_once_with(**data)


def test_receive_support_request_throttling(
    settings: SettingsWrapper,
    api_client: APIClient,
    mocker: MockerFixture,
    db: None,
    is_saas: MagicMock,
) -> None:
    # Given
    settings.HUBSPOT_ACCESS_TOKEN = "some-token"
    mocker.patch(
        "integrations.lead_tracking.hubspot.services.create_self_hosted_onboarding_lead"
    )

    data = {
        "first_name": "user",
        "last_name": "test",
        "email": "user@flagsmith.com",
        "hubspot_cookie": "test-utk",
    }
    url = reverse("api-v1:onboarding:receive-onboarding-request")

    # When
    mocker.patch(
        "onboarding.throttling.get_ip_address_from_request",
        side_effect=["127.0.0.1", "127.0.0.1", "127.0.0.2"],
    )

    # Then - first request should work
    response = api_client.post(url, data=data)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Second request should be throttled(because of the same ip)
    response = api_client.post(url, data=data)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    # Third request should work(because of different ip)
    response = api_client.post(url, data=data)
    assert response.status_code == status.HTTP_204_NO_CONTENT
