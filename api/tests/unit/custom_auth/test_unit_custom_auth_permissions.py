from datetime import timedelta
from typing import Any, Callable

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import (  # type: ignore[attr-defined]
    APIClient,
    override_settings,
)

from organisations.invites.models import Invite, InviteLink
from organisations.models import Organisation


@pytest.fixture
def signup_data() -> dict[str, Any]:
    return {
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
    }


def test_signup_allowed_when_prevent_signup_disabled(
    api_client: APIClient, signup_data: dict[str, Any], db: None
) -> None:
    # Given
    url = reverse("api-v1:custom_auth:ffadminuser-list")

    # When
    response = api_client.post(url, data=signup_data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED


@override_settings(PREVENT_SIGNUP=True)  # type: ignore[misc]
def test_signup_blocked_when_prevent_signup_enabled_and_no_invitation(
    api_client: APIClient, signup_data: dict[str, Any], db: None
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


@override_settings(PREVENT_SIGNUP=True)  # type: ignore[misc]
def test_signup_allowed_with_email_invite(
    api_client: APIClient, signup_data: dict[str, Any], db: None
) -> None:
    # Given
    organisation = Organisation.objects.create(name="Test Org")
    Invite.objects.create(email=signup_data["email"], organisation=organisation)
    url = reverse("api-v1:custom_auth:ffadminuser-list")

    # When
    response = api_client.post(url, data=signup_data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "get_invite_hash, expected_status, expected_detail",
    [
        (
            lambda organisation: InviteLink.objects.create(
                organisation=organisation
            ).hash,
            status.HTTP_201_CREATED,
            None,
        ),
        (
            lambda _: "invalid-hash",
            status.HTTP_403_FORBIDDEN,
            "Signing-up without a valid invitation is disabled. Please contact your administrator.",
        ),
        (
            lambda organisation: InviteLink.objects.create(
                organisation=organisation,
                expires_at=timezone.now() - timedelta(days=1),
            ),
            status.HTTP_403_FORBIDDEN,
            "Signing-up without a valid invitation is disabled. Please contact your administrator.",
        ),
    ],
)
@override_settings(PREVENT_SIGNUP=True)  # type: ignore[misc]
def test_signup_with_invite_hash_behavior(
    api_client: APIClient,
    signup_data: dict[str, Any],
    db: None,
    get_invite_hash: Callable[[Organisation], str],
    expected_status: int,
    expected_detail: str,
    organisation: Organisation,
) -> None:
    # Given
    invite_hash = get_invite_hash(organisation)

    signup_data_with_hash = {**signup_data, "invite_hash": invite_hash}
    url = reverse("api-v1:custom_auth:ffadminuser-list")

    # When
    response = api_client.post(url, data=signup_data_with_hash)

    # Then
    assert response.status_code == expected_status
    if expected_detail:
        assert str(response.data["detail"]) == expected_detail
