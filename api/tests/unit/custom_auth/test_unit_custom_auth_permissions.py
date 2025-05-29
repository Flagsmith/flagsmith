import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, override_settings  # type: ignore[attr-defined]
from datetime import timedelta
from django.utils import timezone

from organisations.invites.models import Invite, InviteLink
from organisations.models import Organisation
from users.models import FFAdminUser


@pytest.fixture
def signup_data():
    return {
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
    }


def test_signup_allowed_when_prevent_signup_disabled(
    api_client: APIClient, signup_data: dict, db: None
) -> None:
    # Given
    url = reverse("api-v1:custom_auth:ffadminuser-list")

    # When
    response = api_client.post(url, data=signup_data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED


@override_settings(PREVENT_SIGNUP=True)
def test_signup_blocked_when_prevent_signup_enabled_and_no_invitation(
    api_client: APIClient, signup_data: dict, db: None
) -> None:
    # Given
    url = reverse("api-v1:custom_auth:ffadminuser-list")

    # When
    response = api_client.post(url, data=signup_data)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        str(response.data["detail"])
        == "Signing-up without a valid invitation is disabled. Please contact your administrator."
    )


@override_settings(PREVENT_SIGNUP=True)
def test_signup_allowed_with_email_invite(
    api_client: APIClient, signup_data: dict, db: None
) -> None:
    # Given
    organisation = Organisation.objects.create(name="Test Org")
    Invite.objects.create(email=signup_data["email"], organisation=organisation)
    url = reverse("api-v1:custom_auth:ffadminuser-list")

    # When
    response = api_client.post(url, data=signup_data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED


@override_settings(PREVENT_SIGNUP=True)
def test_signup_allowed_with_valid_invite_hash(
    api_client: APIClient, signup_data: dict, invite_link: InviteLink, db: None
) -> None:
    # Given
    signup_data_with_hash = {**signup_data, "invite_hash": invite_link.hash}
    url = reverse("api-v1:custom_auth:ffadminuser-list")

    # When
    response = api_client.post(url, data=signup_data_with_hash)

    # Then
    assert response.status_code == status.HTTP_201_CREATED


@override_settings(PREVENT_SIGNUP=True)
def test_signup_blocked_with_invalid_invite_hash(
    api_client: APIClient, signup_data: dict, db: None
) -> None:
    # Given
    signup_data_with_hash = {**signup_data, "invite_hash": "invalid-hash"}
    url = reverse("api-v1:custom_auth:ffadminuser-list")

    # When
    response = api_client.post(url, data=signup_data_with_hash)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        str(response.data["detail"])
        == "Signing-up without a valid invitation is disabled. Please contact your administrator."
    )


@override_settings(PREVENT_SIGNUP=True)
def test_signup_blocked_with_expired_invite_link(
    api_client: APIClient, signup_data: dict, db: None
) -> None:
    # Given
    organisation = Organisation.objects.create(name="Test Org")
    expired_invite_link = InviteLink.objects.create(
        organisation=organisation, expires_at=timezone.now() - timedelta(days=1)
    )
    signup_data_with_hash = {**signup_data, "invite_hash": expired_invite_link.hash}
    url = reverse("api-v1:custom_auth:ffadminuser-list")

    # When
    response = api_client.post(url, data=signup_data_with_hash)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        str(response.data["detail"])
        == "Signing-up without a valid invitation is disabled. Please contact your administrator."
    )
