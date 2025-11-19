import json
import typing

import pytest
from common.environments.permissions import UPDATE_FEATURE_STATE
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from rest_framework import status
from rest_framework.test import APIClient

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureSegment
from features.versioning.versioning_service import (
    get_environment_flags_list,
)
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from tests.types import WithEnvironmentPermissionsCallable


@pytest.fixture()
def sdk_client_factory() -> typing.Callable[[Environment], APIClient]:
    """Factory to create SDK clients for different environments."""

    def _create_sdk_client(environment: Environment) -> APIClient:
        client = APIClient()
        client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
        return client

    return _create_sdk_client


@pytest.fixture()
def sdk_client(
    environment: Environment,
    sdk_client_factory: typing.Callable[[Environment], APIClient],
) -> APIClient:
    """API client configured with SDK authentication for the default environment."""
    return sdk_client_factory(environment)


def get_identity_feature_state_from_sdk(
    sdk_client: APIClient, identifier: str, feature_name: str
) -> typing.Dict[str, typing.Any]:
    """Helper to get a specific feature's state for an identity via SDK endpoint."""
    identities_url = reverse("api-v1:sdk-identities")
    data = {"identifier": identifier}

    response = sdk_client.post(
        identities_url, data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    # Find the specific feature in the flags list
    for flag in response_json["flags"]:
        if flag["feature"]["name"] == feature_name:
            return flag  # type: ignore[no-any-return]

    raise ValueError(f"Feature {feature_name} not found in identity flags response")


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_flag_by_name(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]
    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_id": environment_.id},
    )

    data = {
        "feature": {"name": feature.name},
        "enabled": True,
        "value": {"type": "integer", "string_value": "42"},
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
    assert latest_flags[0].get_feature_state_value() == 42


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
        kwargs={"environment_id": environment_.id},
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
        kwargs={"environment_id": environment_.id},
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
        kwargs={"environment_id": environment_.id},
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
        kwargs={"environment_id": environment_.id},
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
        kwargs={"environment_id": environment_.id},
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
    assert "Feature with identifier 'non_existent_feature' not found" in str(
        response.json()
    )


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
        kwargs={"environment_id": environment_.id},
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
    assert "Feature with identifier '999999' not found" in str(response.json())


# V1 Segment Override Tests


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

    # Create SDK client for this environment
    sdk_client = APIClient()
    sdk_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_.api_key)

    # Create a segment with a rule that matches identities with email containing "test"
    segment = Segment.objects.create(
        name="test_segment", project=project, description="Test segment"
    )
    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(
        rule=segment_rule,
        property="email",
        operator="CONTAINS",
        value="test",
    )

    # Create an identity that matches the segment
    identity = Identity.objects.create(identifier="test_user", environment=environment_)
    identity.update_traits([{"trait_key": "email", "trait_value": "test@example.com"}])

    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_id": environment_.id},
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

    # Verify the segment override is applied to the identity via SDK
    flag_state = get_identity_feature_state_from_sdk(
        sdk_client, identity.identifier, feature.name
    )
    assert flag_state["enabled"] is False
    assert flag_state["feature_state_value"] == 999


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

    # Create SDK client for this environment
    sdk_client = APIClient()
    sdk_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_.api_key)

    # Create a segment with a rule (but no existing feature segment override)
    segment = Segment.objects.create(
        name="new_segment",
        project=project,
        description="New segment for testing creation",
    )
    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(
        rule=segment_rule,
        property="user_type",
        operator="EQUAL",
        value="premium",
    )

    # Verify FeatureSegment doesn't exist yet
    assert not FeatureSegment.objects.filter(
        feature=feature, segment=segment, environment=environment_
    ).exists()

    # Create an identity that matches the segment
    identity = Identity.objects.create(
        identifier="premium_user", environment=environment_
    )
    identity.update_traits([{"trait_key": "user_type", "trait_value": "premium"}])

    url = reverse(
        "api-experiments:update-flag-v1",
        kwargs={"environment_id": environment_.id},
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

    # Verify the segment override was created and is applied via SDK
    flag_state = get_identity_feature_state_from_sdk(
        sdk_client, identity.identifier, feature.name
    )
    assert flag_state["enabled"] is True
    assert flag_state["feature_state_value"] == "premium_feature"


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

    # Create SDK client for this environment
    sdk_client = APIClient()
    sdk_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_.api_key)

    # Create two segments that don't have feature overrides yet
    segment1 = Segment.objects.create(
        name="vip_segment", project=project, description="VIP users"
    )
    segment_rule1 = SegmentRule.objects.create(
        segment=segment1, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(
        rule=segment_rule1,
        property="tier",
        operator="EQUAL",
        value="vip",
    )

    segment2 = Segment.objects.create(
        name="beta_segment", project=project, description="Beta testers"
    )
    segment_rule2 = SegmentRule.objects.create(
        segment=segment2, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(
        rule=segment_rule2,
        property="beta",
        operator="EQUAL",
        value="true",
    )

    # Verify neither FeatureSegment exists yet
    assert not FeatureSegment.objects.filter(
        feature=feature, segment=segment1, environment=environment_
    ).exists()
    assert not FeatureSegment.objects.filter(
        feature=feature, segment=segment2, environment=environment_
    ).exists()

    # Create identities that match the segments
    vip_identity = Identity.objects.create(
        identifier="vip_user", environment=environment_
    )
    vip_identity.update_traits([{"trait_key": "tier", "trait_value": "vip"}])

    beta_identity = Identity.objects.create(
        identifier="beta_user", environment=environment_
    )
    beta_identity.update_traits([{"trait_key": "beta", "trait_value": "true"}])

    url = reverse(
        "api-experiments:update-flag-v2",
        kwargs={"environment_id": environment_.id},
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

    # Verify both segment overrides were created and are applied via SDK
    vip_flag = get_identity_feature_state_from_sdk(
        sdk_client, vip_identity.identifier, feature.name
    )
    assert vip_flag["enabled"] is True
    assert vip_flag["feature_state_value"] == "vip_feature"

    beta_flag = get_identity_feature_state_from_sdk(
        sdk_client, beta_identity.identifier, feature.name
    )
    assert beta_flag["enabled"] is True
    assert beta_flag["feature_state_value"] == "beta_feature"


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
        kwargs={"environment_id": environment_.id},
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
