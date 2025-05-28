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


@pytest.mark.django_db()
def test_get_me_should_return_onboarding_object_without_integrations() -> None:
    # Given
    new_user = FFAdminUser.objects.create(
        email="testuser@mail.com",
        onboarding={
            "tasks": [{"name": "task-1"}],
            "tools": {"completed": True, "integrations": ["integration-1"]},
        },
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
    assert response_json["onboarding"].get("tools", {}).get("integrations") is None
    assert response_json["onboarding"].get("tasks") is not None
    assert response_json["onboarding"].get("tasks", [])[0].get("name") == "task-1"


def test_patch_user_onboarding_returns_403_if_not_from_user(
    staff_user: FFAdminUser, staff_client: APIClient
) -> None:
    # Given
    new_user = FFAdminUser.objects.create(email="testuser@mail.com")
    new_user.save()
    url = reverse("api-v1:custom_auth:ffadminuser-patch-onboarding", args=[new_user.id])

    # When
    response = staff_client.patch(url, data={"tasks": [{"name": "task-1"}]})

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


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
def test_patch_user_onboarding_updates_only_tasks_without_tools(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    data: dict[str, Any],
    expected_keys: set[str],
) -> None:
    # Given
    url = reverse(
        "api-v1:custom_auth:ffadminuser-patch-onboarding", args=[staff_user.id]
    )

    # When
    response = staff_client.patch(url, data=data, format="json")

    # Then
    staff_user.refresh_from_db()

    assert response.status_code == status.HTTP_204_NO_CONTENT
    onboarding = staff_user.onboarding
    assert onboarding is not None
    if "tasks" in expected_keys:
        assert onboarding.get("tasks", [])[0]
        assert onboarding.get("tasks", [])[0].get("name") == data.get("tasks", [])[
            0
        ].get("name")
    if "tools" in expected_keys:
        assert onboarding.get("tools", {}).get("completed") is True
        assert onboarding.get("tools", {}).get("integrations") == data.get(
            "tools", {}
        ).get("integrations")
