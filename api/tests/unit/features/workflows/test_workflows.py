# TODO: this should be moved to the flagsmith-workflows repo but it's easier to write the tests here for development
#  purposes
import json
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from environments.permissions.constants import (
    CREATE_CHANGE_REQUEST,
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.versioning_service import get_environment_flags_dict
from projects.models import Project
from projects.permissions import VIEW_PROJECT
from segments.models import Segment
from tests.types import (
    WithEnvironmentPermissionsCallable,
    WithProjectPermissionsCallable,
)
from users.models import FFAdminUser


@pytest.fixture
def another_segment(project: Project) -> Segment:
    return Segment.objects.create(name="Another segment", project=project)


@pytest.fixture
def another_segment_override(
    environment_v2_versioning: Environment,
    feature: Feature,
    another_segment: Segment,
    staff_user: FFAdminUser,
) -> FeatureState:
    # Since we're using the environment_v2_versioning fixture, we'll need to add the
    # segment override by creating a new version.
    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    feature_state = FeatureState.objects.create(
        environment_feature_version=new_version,
        feature=feature,
        feature_segment=FeatureSegment.objects.create(
            feature=feature,
            segment=another_segment,
            environment=environment_v2_versioning,
        ),
        environment=environment_v2_versioning,
    )
    new_version.publish(published_by=staff_user)
    return feature_state


def test_create_change_request_with_change_set(
    feature: Feature,
    segment: Segment,
    segment_featurestate: FeatureState,
    another_segment: Segment,
    another_segment_override: FeatureState,
    environment_v2_versioning: Environment,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    with_environment_permissions(
        [CREATE_CHANGE_REQUEST, UPDATE_FEATURE_STATE, VIEW_ENVIRONMENT],
        environment_id=environment_v2_versioning.id,
    )
    with_project_permissions([VIEW_PROJECT])

    # Let's generate the data for the change request...
    # we update the default environment feature state to have a new value
    environment_default_update_data = {
        "feature_segment": None,
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "some_updated_value",
        },
    }

    # and create a new segment override
    new_segment = Segment.objects.create(
        name="New segment 1", project=environment_v2_versioning.project
    )
    segment_override_create_data = {
        "feature_segment": {
            "segment": new_segment.id,
            "priority": 1,
        },
        "enabled": True,
        "feature_state_value": {
            "type": "int",
            "integer_value": 42,
        },
    }

    # and update one of the existing segment overrides
    segment_override_update_data = {
        "feature_segment": {
            "segment": segment.id,
            "priority": 2,
        },
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "segment_override_updated_value",
        },
    }

    # and remove the other
    segment_ids_to_delete_overrides = [another_segment.id]

    data = {
        "title": "Test CR",
        "description": "",
        "feature_states": [],
        "environment_feature_versions": [],
        "change_sets": [
            {
                "feature": feature.id,
                "feature_states_to_update": [
                    environment_default_update_data,
                    segment_override_update_data,
                ],
                "feature_states_to_create": [
                    segment_override_create_data,
                ],
                "segment_ids_to_delete_overrides": segment_ids_to_delete_overrides,
            }
        ],
    }

    create_cr_url = reverse(
        "create-change-request", args=[environment_v2_versioning.api_key]
    )
    create_cr_response = staff_client.post(
        create_cr_url, data=json.dumps(data), content_type="application/json"
    )
    assert create_cr_response.status_code == status.HTTP_201_CREATED

    change_request_id = create_cr_response.json()["id"]
    publish_cr_url = reverse(
        "workflows:change-requests-commit",
        args=[change_request_id],
    )
    publish_cr_response = staff_client.post(publish_cr_url)
    assert publish_cr_response.status_code == status.HTTP_200_OK

    # Then
    latest_feature_states = get_environment_flags_dict(
        environment=environment_v2_versioning
    )

    updated_environment_default = latest_feature_states[(feature.id, None, None)]
    assert (
        updated_environment_default.enabled
        == environment_default_update_data["enabled"]
    )
    assert (
        updated_environment_default.get_feature_state_value()
        == environment_default_update_data["feature_state_value"]["string_value"]
    )

    new_segment_override = latest_feature_states[(feature.id, new_segment.id, None)]
    assert new_segment_override.enabled == segment_override_create_data["enabled"]
    assert (
        new_segment_override.get_feature_state_value()
        == segment_override_create_data["feature_state_value"]["integer_value"]
    )
    assert new_segment_override.feature_segment.segment == new_segment
    assert (
        new_segment_override.feature_segment.priority
        == segment_override_create_data["feature_segment"]["priority"]
    )

    updated_segment_override = latest_feature_states[(feature.id, segment.id, None)]
    assert updated_segment_override.enabled == segment_override_update_data["enabled"]
    assert (
        updated_segment_override.get_feature_state_value()
        == segment_override_update_data["feature_state_value"]["string_value"]
    )
    assert updated_segment_override.feature_segment.segment == segment
    assert (
        updated_segment_override.feature_segment.priority
        == segment_override_update_data["feature_segment"]["priority"]
    )

    assert (feature.id, another_segment.id, None) not in latest_feature_states


def test_create_scheduled_change_request_with_change_set(
    feature: Feature,
    feature_state: FeatureState,
    environment_v2_versioning: Environment,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
    mocker: MockerFixture,
) -> None:
    with_environment_permissions(
        [CREATE_CHANGE_REQUEST, UPDATE_FEATURE_STATE, VIEW_ENVIRONMENT],
        environment_id=environment_v2_versioning.id,
    )
    with_project_permissions([VIEW_PROJECT])

    # Let's generate the data for the change request...
    # we update the default environment feature state to have a new value
    environment_default_update_data = {
        "feature_segment": None,
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "some_updated_value",
        },
    }

    # We're going to set a value for live from to ensure that the
    # change request is scheduled for the future instead of immediately
    # on publish
    now = timezone.now()
    one_hour_from_now = now + timedelta(hours=1)

    data = {
        "title": "Test CR",
        "description": "",
        "feature_states": [],
        "environment_feature_versions": [],
        "change_sets": [
            {
                "feature": feature.id,
                "live_from": one_hour_from_now.isoformat(),
                "feature_states_to_update": [
                    environment_default_update_data,
                ],
                "feature_states_to_create": [],
                "segment_ids_to_delete_overrides": [],
            }
        ],
    }

    publish_version_change_set_mock = mocker.patch(
        "features.versioning.tasks.publish_version_change_set"
    )

    create_cr_url = reverse(
        "create-change-request", args=[environment_v2_versioning.api_key]
    )
    create_cr_response = staff_client.post(
        create_cr_url, data=json.dumps(data), content_type="application/json"
    )
    assert create_cr_response.status_code == status.HTTP_201_CREATED
    version_change_set_id = create_cr_response.json()["change_sets"][0]["id"]

    change_request_id = create_cr_response.json()["id"]
    publish_cr_url = reverse(
        "workflows:change-requests-commit",
        args=[change_request_id],
    )
    publish_cr_response = staff_client.post(publish_cr_url)
    assert publish_cr_response.status_code == status.HTTP_200_OK

    # Then
    # The state/value of the environment default feature state hasn't changed
    latest_feature_states = get_environment_flags_dict(
        environment=environment_v2_versioning
    )
    environment_default = latest_feature_states[(feature.id, None, None)]
    assert environment_default.enabled == feature_state.enabled
    assert (
        environment_default.get_feature_state_value()
        == feature_state.get_feature_state_value()
    )

    # and the task was correctly scheduled
    publish_version_change_set_mock.delay.assert_called_once_with(
        kwargs={
            "version_change_set_id": version_change_set_id,
            "user_id": staff_user.id,
            "is_scheduled": True,
        },
        delay_until=one_hour_from_now,
    )


def test_change_request_with_change_set_shows_conflicts_when_changes_made_after_creation(
    feature: Feature,
    environment_v2_versioning: Environment,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    with_environment_permissions(
        [CREATE_CHANGE_REQUEST, UPDATE_FEATURE_STATE, VIEW_ENVIRONMENT],
        environment_id=environment_v2_versioning.id,
    )
    with_project_permissions([VIEW_PROJECT])

    # Let's generate the data for the change requests...
    # In both CRs, we're going update the default environment feature state to
    # have a new value
    cr_1_data, cr_2_data = (
        {
            "title": f"CR{i}",
            "description": "",
            "feature_states": [],
            "environment_feature_versions": [],
            "change_sets": [
                {
                    "feature": feature.id,
                    "feature_states_to_update": [
                        {
                            "feature_segment": None,
                            "enabled": True,
                            "feature_state_value": {
                                "type": "unicode",
                                "string_value": f"some_updated_value_{i}",
                            },
                        },
                    ],
                    "feature_states_to_create": [],
                    "segment_ids_to_delete_overrides": [],
                }
            ],
        }
        for i in range(1, 3)
    )

    create_cr_url = reverse(
        "create-change-request", args=[environment_v2_versioning.api_key]
    )

    # Now let's create the 2 CRs. Creating the 2 CRs should be possible,
    # we only want to check for conflicts on publish.
    create_cr_1_response = staff_client.post(
        create_cr_url, data=json.dumps(cr_1_data), content_type="application/json"
    )
    assert create_cr_1_response.status_code == status.HTTP_201_CREATED
    cr_1_id = create_cr_1_response.json()["id"]

    create_cr_2_response = staff_client.post(
        create_cr_url, data=json.dumps(cr_2_data), content_type="application/json"
    )
    assert create_cr_2_response.status_code == status.HTTP_201_CREATED
    cr_2_id = create_cr_2_response.json()["id"]

    # Now let's publish CR1 which should modify the environment default state
    publish_cr_1_url = reverse(
        "workflows:change-requests-commit",
        args=[cr_1_id],
    )
    publish_cr_1_response = staff_client.post(publish_cr_1_url)
    assert publish_cr_1_response.status_code == status.HTTP_200_OK

    # Now, let's retrieve CR2, which should now include the expected conflict
    retrieve_cr_2_url = reverse(
        "workflows:change-requests-detail",
        args=[cr_2_id],
    )
    retrieve_cr2_response = staff_client.get(retrieve_cr_2_url)
    assert retrieve_cr2_response.status_code == status.HTTP_200_OK

    assert retrieve_cr2_response.json()["conflicts"] == [
        {
            "segment_id": None,
            "original_cr_id": cr_1_id,
            "is_environment_default": True,
        }
    ]

    # But we can still publish CR2
    publish_cr_2_url = reverse(
        "workflows:change-requests-commit",
        args=[cr_2_id],
    )
    publish_cr2_response = staff_client.post(publish_cr_2_url)
    assert publish_cr2_response.status_code == status.HTTP_200_OK
