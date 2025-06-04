import json
from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import FFAdminUser


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


def test_get_me_should_return_onboarding_object(db: None) -> None:
    # Given
    onboarding = {
        "tasks": [{"name": "task-1"}],
        "tools": {"completed": True, "integrations": ["integration-1"]},
    }
    onboarding_serialized = json.dumps(onboarding)
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
    assert response_json["onboarding"] is not None
    assert response_json["onboarding"].get("tools", {}).get("completed") is True
    assert response_json["onboarding"].get("tools", {}).get("integrations") == [
        "integration-1"
    ]
    assert response_json["onboarding"].get("tasks") is not None
    assert response_json["onboarding"].get("tasks", [])[0].get("name") == "task-1"


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
