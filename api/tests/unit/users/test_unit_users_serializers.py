from datetime import datetime

import pytest
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

from users.serializers import (
    OnboardingTaskSerializer,
    PatchOnboardingSerializer,
    UserIdsSerializer,
)


def test_user_ids_serializer_raises_exception_for_invalid_user_id(db: None) -> None:
    # Given
    serializer = UserIdsSerializer(data={"user_ids": [99999]})

    # Then
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)


@freeze_time("2025-01-01T12:00:00Z")
def test_onboarding_task_serializer_list_returns_correct_format() -> None:
    # Given
    data = [
        {"name": "task-1"},
        {"name": "task-2", "completed_at": "2024-01-02T15:00:00Z"},
        {"name": "task-3", "completed_at": None},
    ]

    # When
    serializer = OnboardingTaskSerializer(data=data, many=True)
    assert serializer.is_valid(), serializer.errors

    # Then
    results = serializer.data
    assert results[0]["completed_at"] == datetime.now().isoformat()
    assert results[0]["name"] == "task-1"
    assert results[1]["completed_at"] == "2024-01-02T15:00:00Z"
    assert results[1]["name"] == "task-2"
    assert results[2]["completed_at"] == datetime.now().isoformat()
    assert results[2]["name"] == "task-3"


@pytest.mark.parametrize("tools_completed", [True, False, None])
def test_patch_onboarding_serializer_returns_correct_format(
    tools_completed: bool | None,
) -> None:
    # Given
    data = {
        "tasks": [
            {"name": "task-1", "completed_at": "2024-01-02T15:00:00Z"},
        ],
        "tools": {
            "completed": tools_completed,
            "integrations": ["integration-1", "integration-2"],
        },
    }

    # When
    serializer = PatchOnboardingSerializer(data=data)
    assert serializer.is_valid(), serializer.errors

    # Then
    data = serializer.validated_data
    assert data["tasks"] == [
        {
            "name": "task-1",
            "completed_at": datetime.fromisoformat("2024-01-02T15:00:00Z"),
        },
    ]
    assert data["tools"] == {
        "completed": True if tools_completed is None else tools_completed,
        "integrations": ["integration-1", "integration-2"],
    }


# def test_onboarding_task_to_representation_converts_datetime_to_json_compatible_string() -> (
#     None
# ):
#     # Given
#     serializer = OnboardingTaskSerializer()
#     date = datetime(2025, 1, 1, 12, 0, 0)
#     # When
#     result = serializer.to_representation(
#         {
#             "name": "task-1",
#             "completed_at": date,
#         }
#     )

#     # Then
#     assert isinstance(date, datetime)
#     assert isinstance(result["completed_at"], str)
#     assert result["completed_at"] == "2025-01-01T12:00:00Z"
#     assert result["name"] == "task-1"
