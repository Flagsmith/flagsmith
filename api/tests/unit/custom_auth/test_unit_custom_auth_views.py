import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from django.urls import reverse
from freezegun import freeze_time
from pytest_django.fixtures import SettingsWrapper
from rest_framework import status
from rest_framework.test import APIClient

from users.models import FFAdminUser, HubspotTracker


def test_get_current_user(staff_user: FFAdminUser, staff_client: APIClient) -> None:
    # Given
    url = reverse("api-v1:custom_auth:ffadminuser-me")

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["email"] == staff_user.email
    assert response_json["first_name"] == staff_user.first_name
    assert response_json["last_name"] == staff_user.last_name
    assert response_json["uuid"] == str(staff_user.uuid)


@pytest.mark.parametrize(
    "onboarding_data, expected_response",
    [
        (None, None),
        (
            {"tasks": [{"name": "task-1"}]},
            {"tasks": [{"name": "task-1", "completed_at": "2025-01-01T12:00:00Z"}]},
        ),
        (
            {"tools": {"completed": True, "integrations": ["integration-1"]}},
            {
                "tasks": [],
                "tools": {"completed": True, "integrations": ["integration-1"]},
            },
        ),
        (
            {
                "tasks": [{"name": "task-1"}],
                "tools": {"completed": True, "integrations": ["integration-1"]},
            },
            {
                "tasks": [{"name": "task-1", "completed_at": "2025-01-01T12:00:00Z"}],
                "tools": {"completed": True, "integrations": ["integration-1"]},
            },
        ),
    ],
)
@freeze_time("2025-01-01T12:00:00Z")
def test_get_me_should_return_onboarding_object(
    db: None, onboarding_data: dict[str, Any], expected_response: dict[str, Any]
) -> None:
    # Given
    onboarding_serialized = json.dumps(onboarding_data)
    new_user = FFAdminUser.objects.create(
        email="testuser@mail.com",
        onboarding_data=onboarding_serialized,
    )

    new_user.save()
    client = APIClient()
    client.force_authenticate(user=new_user)
    url = reverse("api-v1:custom_auth:ffadminuser-me")

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["onboarding"] == expected_response


@pytest.mark.parametrize(
    "data,expected_keys",
    [
        (
            {"tasks": [{"name": "task-1", "completed_at": "2024-01-01T12:00:00Z"}]},
            {"tasks"},
        ),
        ({"tools": {"completed": True, "integrations": ["integration-1"]}}, {"tools"}),
        (
            {
                "tasks": [{"name": "task-1", "completed_at": "2024-01-01T12:00:00Z"}],
                "tools": {"completed": True, "integrations": ["integration-1"]},
            },
            {"tasks", "tools"},
        ),
    ],
)
def test_patch_user_onboarding_updates_only_nested_objects_if_provided(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    data: dict[str, Any],
    expected_keys: set[str],
) -> None:
    # Given
    url = reverse("api-v1:custom_auth:ffadminuser-patch-onboarding")

    # When
    response = staff_client.patch(url, data=data, format="json")

    # Then
    staff_user.refresh_from_db()

    assert response.status_code == status.HTTP_204_NO_CONTENT
    onboarding_json = json.loads(staff_user.onboarding_data or "{}")
    assert onboarding_json is not None
    if "tasks" in expected_keys:
        assert onboarding_json.get("tasks", [])[0]
        assert onboarding_json.get("tasks", [])[0].get("name") == data.get("tasks", [])[
            0
        ].get("name")
    if "tools" in expected_keys:
        assert onboarding_json.get("tools", {}).get("completed") is True
        assert onboarding_json.get("tools", {}).get("integrations") == data.get(
            "tools", {}
        ).get("integrations")


def test_patch_user_onboarding_returns_error_if_tasks_and_tools_are_missing(
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:custom_auth:ffadminuser-patch-onboarding")

    # When
    response = staff_client.patch(url, data={}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "non_field_errors": ["At least one of 'tasks' or 'tools' must be provided."]
    }


def test_create_user_calls_hubspot_tracking_and_creates_hubspot_contact(
    mocker: MagicMock,
    db: None,
    settings: SettingsWrapper,
    staff_client: APIClient,
) -> None:
    # Given
    hubspot_cookie = "1234567890"
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    data = {
        "first_name": "new",
        "last_name": "user",
        "email": "test@exemple.fr",
        "password": "password123456!=&",
        "sign_up_type": "NO_INVITE",
        "hubspotutk": hubspot_cookie,
    }

    mock_create_hubspot_contact_for_user = mocker.patch(
        "integrations.lead_tracking.hubspot.services.create_hubspot_contact_for_user"
    )

    url = reverse("api-v1:custom_auth:ffadminuser-list")
    # When
    response = staff_client.post(url, data=data, format="json")

    user = FFAdminUser.objects.filter(email="test@exemple.fr").first()
    hubspot_tracker = HubspotTracker.objects.filter(user=user).first()
    assert hubspot_tracker is not None
    assert hubspot_tracker.hubspot_cookie == hubspot_cookie
    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert user is not None

    mock_create_hubspot_contact_for_user.delay.assert_called_once_with(args=(user.id,))


def test_create_user_does_not_create_hubspot_tracking_if_no_cookie_is_provided(
    mocker: MagicMock,
    db: None,
    settings: SettingsWrapper,
    staff_client: APIClient,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    data = {
        "first_name": "new",
        "last_name": "user",
        "email": "test@exemple.fr",
        "password": "password123456!=&",
        "sign_up_type": "NO_INVITE",
    }

    mock_create_hubspot_contact_for_user = mocker.patch(
        "integrations.lead_tracking.hubspot.services.create_hubspot_contact_for_user"
    )

    url = reverse("api-v1:custom_auth:ffadminuser-list")
    # When
    response = staff_client.post(url, data=data, format="json")

    user = FFAdminUser.objects.filter(email="test@exemple.fr").first()
    hubspot_tracker = HubspotTracker.objects.filter(user=user).first()
    assert hubspot_tracker is None
    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert user is not None

    mock_create_hubspot_contact_for_user.delay.assert_called_once_with(args=(user.id,))
