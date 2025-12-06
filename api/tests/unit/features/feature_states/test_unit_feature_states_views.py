import json
import typing

import pytest
from common.environments.permissions import UPDATE_FEATURE_STATE
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.versioning_service import (
    get_current_live_environment_feature_version,
    get_environment_flags_list,
)
from projects.models import Project
from segments.models import Segment
from tests.types import WithEnvironmentPermissionsCallable


@pytest.mark.parametrize(
    "value_type,string_value,expected_value",
    [
        ("integer", "42", 42),
        ("string", "hello", "hello"),
        ("boolean", "true", True),
    ],
)
@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_flag_by_name(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    value_type: str,
    string_value: str,
    expected_value: typing.Any,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]
    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment_.api_key},
    )

    data = {
        "feature": {"name": feature.name},
        "enabled": True,
        "value": {"type": value_type, "string_value": string_value},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    latest_flags = get_environment_flags_list(
        environment=environment_, feature_name=feature.name
    )

    assert latest_flags[0].enabled is True
    assert latest_flags[0].get_feature_state_value() == expected_value


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_flag_by_id(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]
    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment_.api_key},
    )

    data = {
        "feature": {"id": feature.id},
        "enabled": False,
        "value": {"type": "string", "string_value": "test_value"},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    latest_flags = get_environment_flags_list(
        environment=environment_, feature_name=feature.name
    )

    assert latest_flags[0].enabled is False
    assert latest_flags[0].get_feature_state_value() == "test_value"


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_flag_error_when_both_name_and_id_provided(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]
    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment_.api_key},
    )

    # Providing both name and ID (even if they match the same feature)
    data = {
        "feature": {"name": feature.name, "id": feature.id},
        "enabled": True,
        "value": {"type": "integer", "string_value": "42"},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "feature" in response.json()
    assert "Provide either 'name' or 'id', not both" in str(response.json()["feature"])


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_flag_error_when_both_name_and_id_provided_for_different_features(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    project: Project,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]

    # Create another feature in the same project
    another_feature = Feature.objects.create(
        name="another_feature", project=project, type="STANDARD"
    )

    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment_.api_key},
    )

    # Providing both name and ID for DIFFERENT features (worst case)
    data = {
        "feature": {"name": feature.name, "id": another_feature.id},
        "enabled": True,
        "value": {"type": "integer", "string_value": "42"},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then - Should fail at validation level (mutual exclusion)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "feature" in response.json()
    assert "Provide either 'name' or 'id', not both" in str(response.json()["feature"])


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_flag_error_when_neither_name_nor_id_provided(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]
    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment_.api_key},
    )

    # Providing empty feature object
    data = {
        "feature": {},
        "enabled": True,
        "value": {"type": "integer", "string_value": "42"},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "feature" in response.json()
    assert "Either 'name' or 'id' is required" in str(response.json()["feature"])


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_flag_error_when_feature_not_found_by_name(
    staff_client: APIClient,
    environment_: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]
    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment_.api_key},
    )

    data = {
        "feature": {"name": "non_existent_feature"},
        "enabled": True,
        "value": {"type": "integer", "string_value": "42"},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "not found in project" in str(response.json())


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_flag_error_when_feature_not_found_by_id(
    staff_client: APIClient,
    environment_: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]
    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment_.api_key},
    )

    data = {
        "feature": {"id": 999999},  # Non-existent ID
        "enabled": True,
        "value": {"type": "integer", "string_value": "42"},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "not found in project" in str(response.json())


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_flag_segment_override_by_name(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    project: Project,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]

    segment = Segment.objects.create(
        name="test_segment", project=project, description="Test segment"
    )

    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment_.api_key},
    )

    data = {
        "feature": {"name": feature.name},
        "segment": {"id": segment.id, "priority": 1},
        "enabled": False,
        "value": {"type": "integer", "string_value": "999"},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify the segment override was created
    latest_flags = get_environment_flags_list(
        environment=environment_, feature_name=feature.name
    )
    segment_override = [
        fs
        for fs in latest_flags
        if fs.feature_segment and fs.feature_segment.segment_id == segment.id
    ][0]
    assert segment_override.enabled is False
    assert segment_override.get_feature_state_value() == 999


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_flag_segment_override_creates_feature_segment_if_not_exists(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    project: Project,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]

    segment = Segment.objects.create(
        name="new_segment",
        project=project,
        description="New segment for testing creation",
    )

    # Verify FeatureSegment doesn't exist yet
    assert not FeatureSegment.objects.filter(
        feature=feature, segment=segment, environment=environment_
    ).exists()

    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment_.api_key},
    )

    data = {
        "feature": {"name": feature.name},
        "segment": {"id": segment.id, "priority": 10},
        "enabled": True,
        "value": {"type": "string", "string_value": "premium_feature"},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then - Should succeed and CREATE the FeatureSegment
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify the segment override was created
    latest_flags = get_environment_flags_list(
        environment=environment_, feature_name=feature.name
    )
    segment_override = [
        fs
        for fs in latest_flags
        if fs.feature_segment and fs.feature_segment.segment_id == segment.id
    ][0]
    assert segment_override.enabled is True
    assert segment_override.get_feature_state_value() == "premium_feature"
    assert segment_override.feature_segment is not None
    assert segment_override.feature_segment.priority == 10


def test_create_new_segment_override_reorders_priorities_v1(
    staff_client: APIClient,
    feature: Feature,
    environment: Environment,
    project: Project,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]

    segment1 = Segment.objects.create(name="segment1", project=project)
    segment2 = Segment.objects.create(name="segment2", project=project)

    # Create existing segment override at priority 0
    feature_segment1 = FeatureSegment.objects.create(
        feature=feature,
        segment=segment1,
        environment=environment,
        priority=0,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment1,
        enabled=True,
    )

    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment.api_key},
    )

    # When - Create new segment override at priority 0 (should push segment1 to priority 1)
    data = {
        "feature": {"name": feature.name},
        "segment": {"id": segment2.id, "priority": 0},
        "enabled": True,
        "value": {"type": "string", "string_value": "new_segment_value"},
    }
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Refresh from DB
    feature_segment1.refresh_from_db()
    feature_segment2 = FeatureSegment.objects.get(
        feature=feature, segment=segment2, environment=environment
    )

    # segment2 should be at priority 0, segment1 should have been pushed to priority 1
    assert feature_segment2.priority == 0
    assert feature_segment1.priority == 1


# Update Multiple Feature States Tests


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_feature_states_creates_new_segment_overrides(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    project: Project,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]

    # Create two segments that don't have feature overrides yet
    segment1 = Segment.objects.create(
        name="vip_segment", project=project, description="VIP users"
    )
    segment2 = Segment.objects.create(
        name="beta_segment", project=project, description="Beta testers"
    )

    # Verify neither FeatureSegment exists yet
    assert not FeatureSegment.objects.filter(
        feature=feature, segment=segment1, environment=environment_
    ).exists()
    assert not FeatureSegment.objects.filter(
        feature=feature, segment=segment2, environment=environment_
    ).exists()

    url = reverse(
        "api-experiments:update-flag-v2",
        kwargs={"environment_key": environment_.api_key},
    )

    # Batch update with environment default + 2 new segment overrides
    data = {
        "feature": {"name": feature.name},
        "environment_default": {
            "enabled": False,
            "value": {"type": "string", "string_value": "default"},
        },
        "segment_overrides": [
            {
                "segment_id": segment1.id,
                "priority": 1,
                "enabled": True,
                "value": {"type": "string", "string_value": "vip_feature"},
            },
            {
                "segment_id": segment2.id,
                "priority": 2,
                "enabled": True,
                "value": {"type": "string", "string_value": "beta_feature"},
            },
        ],
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify both segment overrides were created
    latest_flags = get_environment_flags_list(
        environment=environment_, feature_name=feature.name
    )

    vip_override = [
        fs
        for fs in latest_flags
        if fs.feature_segment and fs.feature_segment.segment_id == segment1.id
    ][0]
    assert vip_override.enabled is True
    assert vip_override.get_feature_state_value() == "vip_feature"

    beta_override = [
        fs
        for fs in latest_flags
        if fs.feature_segment and fs.feature_segment.segment_id == segment2.id
    ][0]
    assert beta_override.enabled is True
    assert beta_override.get_feature_state_value() == "beta_feature"


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_feature_states_environment_default_only(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]
    url = reverse(
        "api-experiments:update-flag-v2",
        kwargs={"environment_key": environment_.api_key},
    )

    # Test with just environment default (no segment overrides)
    data = {
        "feature": {"name": feature.name},
        "environment_default": {
            "enabled": True,
            "value": {"type": "integer", "string_value": "100"},
        },
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify the actual state in the database
    latest_flags = get_environment_flags_list(
        environment=environment_, feature_name=feature.name
    )

    # Find environment default
    env_default = [fs for fs in latest_flags if fs.feature_segment is None][0]
    assert env_default.enabled is True
    assert env_default.get_feature_state_value() == 100


def test_update_feature_states_rejects_duplicate_segment_ids(
    staff_client: APIClient,
    feature: Feature,
    environment: Environment,
    project: Project,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]

    segment1 = Segment.objects.create(name="segment1", project=project)

    url = reverse(
        "api-experiments:update-flag-v2",
        kwargs={"environment_key": environment.api_key},
    )

    # Request with duplicate segment_id
    data = {
        "feature": {"name": feature.name},
        "environment_default": {
            "enabled": True,
            "value": {"type": "string", "string_value": "default"},
        },
        "segment_overrides": [
            {
                "segment_id": segment1.id,
                "enabled": True,
                "value": {"type": "string", "string_value": "value1"},
            },
            {
                "segment_id": segment1.id,  # Duplicate!
                "enabled": False,
                "value": {"type": "string", "string_value": "value2"},
            },
        ],
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Duplicate segment_id values are not allowed" in str(response.json())


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_existing_segment_override_with_priority_v1(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    project: Project,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    """Test updating an existing segment override with a new priority using V1 endpoint."""
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]

    segment = Segment.objects.create(name="priority_segment", project=project)

    # Create the segment override manually
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment_,
        priority=5,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment_,
        feature_segment=feature_segment,
        enabled=True,
    )

    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment_.api_key},
    )

    # When - Update the same segment override with new priority
    update_data = {
        "feature": {"name": feature.name},
        "segment": {"id": segment.id, "priority": 1},  # Changed priority
        "enabled": False,  # Changed enabled
        "value": {"type": "integer", "string_value": "200"},  # Changed value
    }
    response = staff_client.post(
        url, data=json.dumps(update_data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify the update - get the latest feature segment (V2 versioning creates new ones)
    feature_segment = (
        FeatureSegment.objects.filter(
            feature=feature, segment=segment, environment=environment_
        )
        .order_by("-id")
        .first()
    )
    assert feature_segment is not None
    assert feature_segment.priority == 1


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_existing_segment_override_with_priority_v2(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    project: Project,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    """Test updating an existing segment override with a new priority using V2 endpoint."""
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]

    segment = Segment.objects.create(name="priority_segment_v2", project=project)

    # Create the segment override manually
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment_,
        priority=5,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment_,
        feature_segment=feature_segment,
        enabled=True,
    )

    # When - Update the existing segment override using V2 endpoint
    v2_url = reverse(
        "api-experiments:update-flag-v2",
        kwargs={"environment_key": environment_.api_key},
    )
    update_data = {
        "feature": {"name": feature.name},
        "environment_default": {
            "enabled": True,
            "value": {"type": "string", "string_value": "default"},
        },
        "segment_overrides": [
            {
                "segment_id": segment.id,
                "priority": 2,  # Changed priority
                "enabled": False,  # Changed enabled
                "value": {"type": "string", "string_value": "updated"},
            },
        ],
    }
    response = staff_client.post(
        v2_url, data=json.dumps(update_data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify the priority was updated - get the latest feature segment
    feature_segment = (
        FeatureSegment.objects.filter(
            feature=feature, segment=segment, environment=environment_
        )
        .order_by("-id")
        .first()
    )
    assert feature_segment is not None
    assert feature_segment.priority == 2


def test_create_new_segment_override_reorders_priorities_v2(
    staff_client: APIClient,
    feature: Feature,
    environment: Environment,
    project: Project,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]

    segment1 = Segment.objects.create(name="segment1_v2", project=project)
    segment2 = Segment.objects.create(name="segment2_v2", project=project)

    # Create existing segment override at priority 0
    feature_segment1 = FeatureSegment.objects.create(
        feature=feature,
        segment=segment1,
        environment=environment,
        priority=0,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment1,
        enabled=True,
    )

    url = reverse(
        "api-experiments:update-flag-v2",
        kwargs={"environment_key": environment.api_key},
    )

    # When - Create new segment override at priority 0 (should push segment1 to priority 1)
    data = {
        "feature": {"name": feature.name},
        "environment_default": {
            "enabled": True,
            "value": {"type": "string", "string_value": "default"},
        },
        "segment_overrides": [
            {
                "segment_id": segment2.id,
                "priority": 0,
                "enabled": True,
                "value": {"type": "string", "string_value": "new_segment_value"},
            },
        ],
    }
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Refresh from DB
    feature_segment1.refresh_from_db()
    feature_segment2 = FeatureSegment.objects.get(
        feature=feature, segment=segment2, environment=environment
    )

    # segment2 should be at priority 0, segment1 should have been pushed to priority 1
    assert feature_segment2.priority == 0
    assert feature_segment1.priority == 1


def test_update_flag_v1_returns_403_when_workflow_enabled(
    staff_client: APIClient,
    feature: Feature,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]
    environment.minimum_change_request_approvals = 1
    environment.save()

    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment.api_key},
    )

    data = {
        "feature": {"name": feature.name},
        "enabled": True,
        "value": {"type": "string", "string_value": "test"},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "change requests are enabled" in str(response.json())


def test_update_flag_v2_returns_403_when_workflow_enabled(
    staff_client: APIClient,
    feature: Feature,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]
    environment.minimum_change_request_approvals = 1
    environment.save()

    url = reverse(
        "api-experiments:update-flag-v2",
        kwargs={"environment_key": environment.api_key},
    )

    data = {
        "feature": {"name": feature.name},
        "environment_default": {
            "enabled": True,
            "value": {"type": "string", "string_value": "test"},
        },
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "change requests are enabled" in str(response.json())


def test_update_existing_segment_override_v2_versioning(
    staff_client: APIClient,
    feature: Feature,
    environment_v2_versioning: Environment,
    project: Project,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]

    segment = Segment.objects.create(name="existing_segment", project=project)

    # Get the current live version and create segment override associated with it
    current_version = get_current_live_environment_feature_version(
        environment_v2_versioning.id, feature.id
    )
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment_v2_versioning,
        priority=5,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment_v2_versioning,
        feature_segment=feature_segment,
        environment_feature_version=current_version,
        enabled=True,
    )

    url = reverse(
        "api-experiments:update-flag-v2",
        kwargs={"environment_key": environment_v2_versioning.api_key},
    )

    # When - Update the existing segment override
    data = {
        "feature": {"name": feature.name},
        "environment_default": {
            "enabled": True,
            "value": {"type": "string", "string_value": "default"},
        },
        "segment_overrides": [
            {
                "segment_id": segment.id,
                "priority": 1,  # Changed priority from 5 to 1
                "enabled": False,  # Changed enabled from True to False
                "value": {"type": "integer", "string_value": "999"},
            },
        ],
    }
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify the segment override was updated
    latest_flags = get_environment_flags_list(
        environment=environment_v2_versioning, feature_name=feature.name
    )
    segment_override = [
        fs
        for fs in latest_flags
        if fs.feature_segment and fs.feature_segment.segment_id == segment.id
    ][0]

    assert segment_override.enabled is False
    assert segment_override.get_feature_state_value() == 999
    assert segment_override.feature_segment is not None
    assert segment_override.feature_segment.priority == 1


def test_update_flag_v1_returns_403_without_permission(
    staff_client: APIClient,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given - no permissions granted
    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": environment.api_key},
    )

    data = {
        "feature": {"name": feature.name},
        "enabled": True,
        "value": {"type": "string", "string_value": "test"},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_flag_v2_returns_403_without_permission(
    staff_client: APIClient,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given - no permissions granted
    url = reverse(
        "api-experiments:update-flag-v2",
        kwargs={"environment_key": environment.api_key},
    )

    data = {
        "feature": {"name": feature.name},
        "environment_default": {
            "enabled": True,
            "value": {"type": "string", "string_value": "test"},
        },
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_flag_v1_returns_403_for_nonexistent_environment(
    staff_client: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_key": "nonexistent_key"},
    )

    data = {
        "feature": {"name": "any_feature"},
        "enabled": True,
        "value": {"type": "string", "string_value": "test"},
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
