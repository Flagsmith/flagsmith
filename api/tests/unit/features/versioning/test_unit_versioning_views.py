import json
import typing
from datetime import datetime, timedelta

import pytest
from common.environments.permissions import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from common.projects.permissions import VIEW_PROJECT
from core.constants import STRING
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from freezegun.api import FrozenDateTimeFactory
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from api_keys.models import MasterAPIKey
from audit.constants import ENVIRONMENT_FEATURE_VERSION_PUBLISHED_MESSAGE
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from features.feature_segments.limits import (
    SEGMENT_OVERRIDE_LIMIT_EXCEEDED_MESSAGE,
)
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.versioning.constants import DEFAULT_VERSION_LIMIT_DAYS
from features.versioning.models import EnvironmentFeatureVersion
from organisations.models import (
    OrganisationSubscriptionInformationCache,
    Subscription,
)
from organisations.subscriptions.constants import SubscriptionPlanFamily
from projects.models import Project
from segments.models import Segment
from tests.types import (
    WithEnvironmentPermissionsCallable,
    WithProjectPermissionsCallable,
)
from users.models import FFAdminUser

now = timezone.now()
tomorrow = now + timedelta(days=1)


def test_get_versions_for_a_feature_and_environment(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    environment_v2_versioning: Environment,
    feature: Feature,
) -> None:
    # Given
    url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    # the initial version created automatically
    version_1 = EnvironmentFeatureVersion.objects.get(
        feature=feature, environment=environment_v2_versioning
    )

    # create a second published version
    version_2 = EnvironmentFeatureVersion.objects.create(
        feature=feature, environment=environment_v2_versioning
    )
    version_2.publish(published_by=admin_user)

    # and a draft version
    draft_version = EnvironmentFeatureVersion.objects.create(
        feature=feature, environment=environment_v2_versioning
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3

    uuids = {result["uuid"] for result in response_json["results"]}
    assert len(uuids) == 3
    assert all(
        str(version.uuid) in uuids for version in (version_1, version_2, draft_version)
    )


def test_create_new_feature_version(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    environment_v2_versioning: Environment,
    feature: Feature,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE])
    with_project_permissions([VIEW_PROJECT])

    url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    # When
    response = staff_client.post(url)

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    response_json = response.json()
    assert response_json["created_by"] == staff_user.id
    assert response_json["uuid"]


def test_delete_feature_version(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    feature: Feature,
) -> None:
    # Given
    # an unpublished version
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    url = reverse(
        "api-v1:versioning:environment-feature-versions-detail",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
        ],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    environment_feature_version.refresh_from_db()
    assert environment_feature_version.deleted is True


def test_retrieve_environment_feature_version_permission_denied(
    feature: Feature,
    environment_v2_versioning: Environment,
    staff_client: APIClient,
) -> None:
    # Given
    efv = EnvironmentFeatureVersion.objects.first()

    url = reverse("api-v1:versioning:get-efv-by-uuid", args=[str(efv.uuid)])

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_retrieve_feature_version_with_no_previous_version(
    feature: Feature,
    environment_v2_versioning: Environment,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    environment_feature_version = EnvironmentFeatureVersion.objects.get(
        feature=feature, environment=environment_v2_versioning
    )

    url = reverse(
        "api-v1:versioning:get-efv-by-uuid", args=[environment_feature_version.uuid]
    )

    with_environment_permissions([VIEW_ENVIRONMENT])
    with_project_permissions([VIEW_PROJECT])

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["uuid"] == str(environment_feature_version.uuid)
    assert response_json["previous_version_uuid"] is None
    assert response_json["feature"] == feature.id
    assert response_json["environment"] == environment_v2_versioning.id


def test_retrieve_feature_version_with_previous_version(
    feature: Feature,
    environment_v2_versioning: Environment,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])
    with_project_permissions([VIEW_PROJECT])

    version_1 = EnvironmentFeatureVersion.objects.filter(
        feature=feature, environment=environment_v2_versioning
    ).get()
    version_2 = EnvironmentFeatureVersion.objects.create(
        feature=feature, environment=environment_v2_versioning
    )
    version_2.publish(published_by=staff_user)

    url = reverse("api-v1:versioning:get-efv-by-uuid", args=[version_2.uuid])

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["uuid"] == str(version_2.uuid)
    assert response_json["previous_version_uuid"] == str(version_1.uuid)


def test_retrieve_feature_version_for_unpublished_version(
    feature: Feature,
    environment_v2_versioning: Environment,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])
    with_project_permissions([VIEW_PROJECT])

    version_1 = EnvironmentFeatureVersion.objects.filter(
        feature=feature, environment=environment_v2_versioning
    ).get()
    version_2 = EnvironmentFeatureVersion.objects.create(
        feature=feature, environment=environment_v2_versioning
    )

    url = reverse("api-v1:versioning:get-efv-by-uuid", args=[version_2.uuid])

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["uuid"] == str(version_2.uuid)
    assert response_json["previous_version_uuid"] == str(version_1.uuid)


def test_cannot_delete_live_feature_version(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    feature: Feature,
) -> None:
    # Given
    # the initial published version
    environment_feature_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )

    url = reverse(
        "api-v1:versioning:environment-feature-versions-detail",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
        ],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert response.json()["detail"] == "Cannot delete a live version."


@pytest.mark.parametrize("live_from", (None, tomorrow))
def test_publish_feature_version(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    environment_v2_versioning: Environment,
    feature: Feature,
    live_from: typing.Optional[datetime],
) -> None:
    # Given
    # an unpublished version
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    url = reverse(
        "api-v1:versioning:environment-feature-versions-publish",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
        ],
    )

    # When
    with freeze_time(now):
        response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    environment_feature_version.refresh_from_db()
    assert environment_feature_version.is_live is True
    assert environment_feature_version.published is True
    assert environment_feature_version.published_by == admin_user
    assert (
        environment_feature_version.live_from == now if live_from is None else live_from
    )

    # and an audit log record is created correctly
    record = AuditLog.objects.filter(
        related_object_type=RelatedObjectType.EF_VERSION.name,
        related_object_uuid=environment_feature_version.uuid,
    ).first()
    assert record
    assert record.log == ENVIRONMENT_FEATURE_VERSION_PUBLISHED_MESSAGE % feature.name


@pytest.mark.parametrize("live_from", (None, tomorrow))
def test_publish_feature_version_using_master_api_key(
    admin_master_api_key: MasterAPIKey,
    admin_master_api_key_client: APIClient,
    environment_v2_versioning: Environment,
    feature: Feature,
    live_from: datetime | None,
) -> None:
    # Given
    # an unpublished version
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    url = reverse(
        "api-v1:versioning:environment-feature-versions-publish",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
        ],
    )

    # When
    with freeze_time(now):
        response = admin_master_api_key_client.post(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    environment_feature_version.refresh_from_db()
    assert environment_feature_version.is_live is True
    assert environment_feature_version.published is True
    assert environment_feature_version.published_by is None
    assert environment_feature_version.published_by_api_key == admin_master_api_key[0]
    assert (
        environment_feature_version.live_from == now if live_from is None else live_from
    )


def test_list_environment_feature_version_feature_states(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    feature: Feature,
) -> None:
    # Given
    environment_feature_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )

    url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-list",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
        ],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 1


def test_add_environment_feature_version_feature_state(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    segment: Segment,
    feature: Feature,
) -> None:
    # Given
    # an unpublished environment feature version
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-list",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
        ],
    )

    data = {
        "feature_segment": {"segment": segment.id},
        "enabled": True,
        "feature_state_value": {
            "string_value": "segment value!",
        },
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    assert environment_feature_version.feature_states.count() == 2
    assert environment_feature_version.feature_segments.count() == 1


def test_cannot_add_feature_state_to_published_environment_feature_version(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    segment: Segment,
    feature: Feature,
) -> None:
    # Given
    # the initial (published) environment feature version
    environment_feature_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )

    url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-list",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
        ],
    )

    data = {
        "feature_segment": {"segment": segment.id},
        "enabled": True,
        "feature_state_value": {
            "string_value": "segment value!",
        },
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert environment_feature_version.feature_states.count() == 1

    assert response.json()["detail"] == "Cannot modify published version."


def test_update_environment_feature_version_feature_state(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    feature: Feature,
) -> None:
    # Given
    # an unpublished environment feature version
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # and the environment feature state for the feature, environment, version combination
    feature_state = environment_feature_version.feature_states.filter(
        feature=feature,
        environment=environment_v2_versioning,
        feature_segment__isnull=True,
        identity__isnull=True,
    ).get()
    assert feature_state.enabled is False

    url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-detail",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
            feature_state.id,
        ],
    )

    # When
    response = admin_client.patch(
        url, data=json.dumps({"enabled": True}), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    feature_state.refresh_from_db()
    assert feature_state.enabled is True


def test_cannot_update_feature_state_in_published_environment_feature_version(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    feature: Feature,
) -> None:
    # Given
    # the initial (published) environment feature version
    environment_feature_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )

    # and the environment feature state for the feature, environment, version combination
    feature_state = environment_feature_version.feature_states.filter(
        feature=feature,
        environment=environment_v2_versioning,
        feature_segment__isnull=True,
        identity__isnull=True,
    ).get()
    assert feature_state.enabled is False

    url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-detail",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
            feature_state.id,
        ],
    )

    # When
    response = admin_client.patch(
        url, data=json.dumps({"enabled": True}), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert response.json()["detail"] == "Cannot modify published version."

    feature_state.refresh_from_db()
    assert feature_state.enabled is False


def test_delete_environment_feature_version_feature_state(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    segment: Segment,
    feature: Feature,
) -> None:
    # Given
    # an unpublished environment feature version
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # and a Segment override feature state in the feature version
    segment_override = FeatureState.objects.create(
        environment_feature_version=environment_feature_version,
        feature=feature,
        environment=environment_v2_versioning,
        feature_segment=FeatureSegment.objects.create(
            feature=feature, environment=environment_v2_versioning, segment=segment
        ),
    )

    url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-detail",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
            segment_override.id,
        ],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    segment_override.refresh_from_db()
    assert segment_override.deleted is True


def test_cannot_delete_feature_state_in_published_environment_feature_version(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    environment_v2_versioning: Environment,
    segment: Segment,
    feature: Feature,
) -> None:
    # Given
    # an unpublished environment feature version
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # and a Segment override feature state in the feature version
    segment_override = FeatureState.objects.create(
        environment_feature_version=environment_feature_version,
        feature=feature,
        environment=environment_v2_versioning,
        feature_segment=FeatureSegment.objects.create(
            feature=feature, environment=environment_v2_versioning, segment=segment
        ),
    )

    # and we publish the version
    environment_feature_version.publish(admin_user)

    url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-detail",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
            segment_override.id,
        ],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert response.json()["detail"] == "Cannot modify published version."

    segment_override.refresh_from_db()
    assert segment_override.deleted is False


def test_cannot_delete_environment_default_feature_state_for_unpublished_environment_feature_version(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    feature: Feature,
) -> None:
    # Given
    # an unpublished environment feature version
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # and the environment default feature state in the feature version
    segment_override = FeatureState.objects.get(
        environment_feature_version=environment_feature_version,
        feature=feature,
        environment=environment_v2_versioning,
        feature_segment__isnull=True,
        identity__isnull=True,
    )

    url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-detail",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
            segment_override.id,
        ],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert (
        response.json()["detail"] == "Cannot delete environment default feature state."
    )

    segment_override.refresh_from_db()
    assert segment_override.deleted is False


def test_filter_versions_by_is_live(
    environment_v2_versioning: Environment,
    feature: Feature,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    # we give the user the correct permissions
    with_environment_permissions([VIEW_ENVIRONMENT], environment_v2_versioning.id)
    with_project_permissions([VIEW_PROJECT])

    # an unpublished environment feature version
    unpublished_environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # and a published version
    published_environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    published_environment_feature_version.publish(staff_user)

    _base_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )
    live_versions_url = "%s?is_live=true" % _base_url
    not_live_versions_url = "%s?is_live=false" % _base_url

    # When
    live_versions_response = staff_client.get(live_versions_url)
    not_live_versions_response = staff_client.get(not_live_versions_url)

    # Then
    # only the live versions are returned (the initial version) and the one we
    # published above when we request the live versions
    assert live_versions_response.status_code == status.HTTP_200_OK

    live_versions_response_json = live_versions_response.json()
    assert live_versions_response_json["count"] == 2
    assert unpublished_environment_feature_version.uuid not in [
        result["uuid"] for result in live_versions_response_json["results"]
    ]

    # and only the unpublished version is returned when we request the 'not live' versions
    assert not_live_versions_response.status_code == status.HTTP_200_OK

    not_live_versions_response_json = not_live_versions_response.json()
    assert not_live_versions_response_json["count"] == 1
    assert not_live_versions_response_json["results"][0]["uuid"] == str(
        unpublished_environment_feature_version.uuid
    )


def test_disable_v2_versioning_returns_bad_request_if_not_using_v2_versioning(
    environment: Environment,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-disable-v2-versioning",
        args=[environment.api_key],
    )

    with_environment_permissions(
        permission_keys=[], environment_id=environment.id, admin=True
    )

    # When
    response = staff_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_new_version_with_changes_in_single_request(
    feature: Feature,
    segment: Segment,
    segment_featurestate: FeatureState,
    admin_client_new: APIClient,
    environment_v2_versioning: Environment,
) -> None:
    # Given
    additional_segment_1 = Segment.objects.create(
        name="additional-segment-1", project=feature.project
    )
    additional_segment_2 = Segment.objects.create(
        name="additional-segment-2", project=feature.project
    )

    url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    data = {
        "publish_immediately": True,
        "feature_states_to_update": [
            {
                "feature_segment": None,
                "enabled": True,
                "feature_state_value": {"type": "unicode", "string_value": "updated!"},
            }
        ],
        "feature_states_to_create": [
            {
                "feature_segment": {
                    "segment": additional_segment_1.id,
                    "priority": 2,
                },
                "enabled": True,
                "feature_state_value": {
                    "type": "unicode",
                    "string_value": "segment-override-1",
                },
            },
            {
                "feature_segment": {
                    "segment": additional_segment_2.id,
                    "priority": 1,
                },
                "enabled": True,
                "feature_state_value": {
                    "type": "unicode",
                    "string_value": "segment-override-2",
                },
            },
        ],
        "segment_ids_to_delete_overrides": [segment.id],
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    new_version_uuid = response.json()["uuid"]
    new_version = EnvironmentFeatureVersion.objects.get(uuid=new_version_uuid)

    assert new_version.feature_states.count() == 3

    new_version_environment_fs = new_version.feature_states.filter(
        feature_segment__isnull=True
    ).get()
    assert new_version_environment_fs.get_feature_state_value() == "updated!"
    assert new_version_environment_fs.enabled is True

    new_version_segment_fs_1 = new_version.feature_states.filter(
        feature_segment__segment=additional_segment_1
    ).get()
    assert new_version_segment_fs_1.get_feature_state_value() == "segment-override-1"
    assert new_version_segment_fs_1.enabled is True
    assert new_version_segment_fs_1.feature_segment.priority == 2

    new_version_segment_fs_2 = new_version.feature_states.filter(
        feature_segment__segment=additional_segment_2
    ).get()
    assert new_version_segment_fs_2.get_feature_state_value() == "segment-override-2"
    assert new_version_segment_fs_2.enabled is True
    assert new_version_segment_fs_2.feature_segment.priority == 1

    assert not new_version.feature_states.filter(
        feature_segment__segment=segment
    ).exists()

    assert new_version.published is True
    assert new_version.is_live is True


def test_update_and_create_segment_override_in_single_request(
    feature: Feature,
    segment: Segment,
    segment_featurestate: FeatureState,
    admin_client_new: APIClient,
    environment_v2_versioning: Environment,
) -> None:
    # Given
    additional_segment = Segment.objects.create(
        name="additional-segment", project=feature.project
    )

    url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    data = {
        "publish_immediately": True,
        "feature_states_to_update": [
            {
                "feature_segment": {"segment": segment.id, "priority": 2},
                "enabled": True,
                "feature_state_value": {
                    "type": "unicode",
                    "string_value": "updated-segment-override",
                },
            }
        ],
        "feature_states_to_create": [
            {
                "feature_segment": {
                    "segment": additional_segment.id,
                    "priority": 1,
                },
                "enabled": True,
                "feature_state_value": {
                    "type": "unicode",
                    "string_value": "additional-segment-override",
                },
            },
        ],
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    new_version_uuid = response.json()["uuid"]
    new_version = EnvironmentFeatureVersion.objects.get(uuid=new_version_uuid)

    assert new_version.feature_states.count() == 3

    updated_segment_override = new_version.feature_states.filter(
        feature_segment__segment=segment
    ).get()
    assert (
        updated_segment_override.get_feature_state_value() == "updated-segment-override"
    )
    assert updated_segment_override.enabled is True
    assert updated_segment_override.feature_segment.priority == 2

    new_segment_override = new_version.feature_states.filter(
        feature_segment__segment=additional_segment
    ).get()
    assert (
        new_segment_override.get_feature_state_value() == "additional-segment-override"
    )
    assert new_segment_override.enabled is True
    assert new_segment_override.feature_segment.priority == 1

    assert new_version.published is True
    assert new_version.is_live is True


def test_create_environment_default_when_creating_new_version_fails(
    environment_v2_versioning: Environment,
    feature: Feature,
    admin_client_new: APIClient,
) -> None:
    # Given
    data = {
        "feature_states_to_create": [
            {
                "feature_segment": None,
                "enabled": True,
                "feature_state_value": {
                    "type": "unicode",
                    "string_value": "some new value",
                },
            }
        ]
    }

    url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert response.json() == {
        "message": "Cannot create FeatureState objects that are not segment overrides."
    }


def test_create_segment_override_for_existing_override_when_creating_new_version_fails(
    feature: Feature,
    admin_client_new: APIClient,
    segment: Segment,
    segment_featurestate: FeatureState,
    environment_v2_versioning: Environment,
) -> None:
    # Given
    data = {
        "feature_states_to_create": [
            {
                "feature_segment": {"segment": segment.id},
                "enabled": True,
                "feature_state_value": {
                    "type": "unicode",
                    "string_value": "some new value",
                },
            }
        ]
    }

    url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "message": "An unresolvable conflict occurred: segment override already exists for segment '%s'"
        % segment.name
    }


def test_create_new_version_for_multivariate_feature(
    multivariate_feature: Feature,
    multivariate_options: list[MultivariateFeatureOption],
    environment_v2_versioning: Environment,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions(
        [VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE], environment_v2_versioning.id
    )
    with_project_permissions([VIEW_PROJECT])

    create_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, multivariate_feature.id],
    )

    data = {
        "feature_states_to_update": [
            {
                "feature_segment": None,
                "enabled": True,
                "feature_state_value": {
                    "type": STRING,
                    "string_value": multivariate_feature.initial_value,
                },
                "multivariate_feature_state_values": [
                    {
                        "multivariate_feature_option": mvfo.id,
                        "percentage_allocation": 10,
                    }
                    for mvfo in multivariate_options
                ],
            }
        ]
    }

    # When
    response = staff_client.post(
        create_version_url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    version_uuid = response.json()["uuid"]
    new_version = EnvironmentFeatureVersion.objects.get(uuid=version_uuid)

    assert all(
        [
            mvfsv.percentage_allocation == 10
            for mvfsv in new_version.feature_states.get(
                feature=multivariate_feature
            ).multivariate_feature_state_values.all()
        ]
    )


def test_create_new_version_delete_segment_override_updates_overrides_immediately(
    feature: Feature,
    segment: Segment,
    feature_segment: FeatureSegment,
    segment_featurestate: FeatureState,
    environment_v2_versioning: Environment,
    admin_client: APIClient,
) -> None:
    # Given
    create_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    data = {
        "segment_ids_to_delete_overrides": [segment.id],
        "publish_immediately": True,
    }

    # When
    response = admin_client.post(
        create_version_url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    get_feature_segments_url = "%s?environment=%d&feature=%d" % (
        reverse("api-v1:features:feature-segment-list"),
        environment_v2_versioning.id,
        feature.id,
    )
    get_feature_segments_response = admin_client.get(get_feature_segments_url)
    assert get_feature_segments_response.status_code == status.HTTP_200_OK
    assert get_feature_segments_response.json()["count"] == 0


def test_creating_multiple_segment_overrides_in_multiple_versions_sets_correct_priorities(
    feature: Feature,
    environment_v2_versioning: Environment,
    segment: Segment,
    another_segment: Segment,
    admin_client_new: APIClient,
) -> None:
    """
    This test is for a specific case found by a customer where creating
    multiple segment overrides consecutively ended up with the 2 segment
    overrides having the same priority.

    This was really caused by slightly odd behaviour from the FE which
    tried to update the existing segment override at the same time as
    creating the new one, but this test ensures that the priorities
    are set correct even in this case.

    See PR here for FE fix: https://github.com/Flagsmith/flagsmith/pull/4609
    """

    def generate_segment_override_fs_payload(
        segment: Segment, priority: int
    ) -> dict[str, typing.Any]:
        return {
            "enabled": True,
            "feature_state_value": {
                "string_value": f"override for segment {segment.name}",
                "type": "unicode",
            },
            "feature_segment": {
                "segment": segment.id,
                "priority": priority,
            },
        }

    url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    # Now, let's create the first override with priority 0
    data = {
        "publish_immediately": True,
        "feature_states_to_create": [generate_segment_override_fs_payload(segment, 0)],
    }
    create_segment_override_1_response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    assert create_segment_override_1_response.status_code == status.HTTP_201_CREATED
    version_1_uuid = create_segment_override_1_response.json()["uuid"]
    assert (
        FeatureSegment.objects.get(
            environment_feature_version__uuid=version_1_uuid,
            feature=feature,
            segment=segment,
        ).priority
        == 0
    )

    # Now, let's create the second override with priority 1 and (to mimic the FE behaviour)
    # update the existing segment override (without actually changing anything).
    data = {
        "publish_immediately": True,
        "feature_states_to_create": [
            generate_segment_override_fs_payload(another_segment, 1)
        ],
        "feature_states_to_update": [generate_segment_override_fs_payload(segment, 0)],
    }
    create_segment_override_2_response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    assert create_segment_override_2_response.status_code == status.HTTP_201_CREATED
    version_2_uuid = create_segment_override_2_response.json()["uuid"]
    assert (
        FeatureSegment.objects.get(
            environment_feature_version__uuid=version_2_uuid,
            feature=feature,
            segment=another_segment,
        ).priority
        == 1
    )


def test_create_new_version_fails_when_breaching_segment_override_limit(
    feature: Feature,
    segment: Segment,
    another_segment: Segment,
    environment_v2_versioning: Environment,
    project: Project,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE])
    with_project_permissions([VIEW_PROJECT])

    # We update the limit of segment overrides on the project
    project.max_segment_overrides_allowed = 1
    project.save()

    # And we create an existing version with a segment override in it
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=version_2,
        feature_segment=FeatureSegment.objects.create(
            feature=feature,
            segment=segment,
            environment=environment_v2_versioning,
            environment_feature_version=version_2,
        ),
    )
    version_2.publish()

    data = {
        "publish_immediately": True,
        "feature_states_to_create": [
            {
                "feature_segment": {"segment": segment.id},
                "enabled": True,
                "feature_state_value": {
                    "type": "unicode",
                    "string_value": "some new value",
                },
            }
        ],
    }
    create_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    # When
    create_version_response = staff_client.post(
        create_version_url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert create_version_response.status_code == status.HTTP_400_BAD_REQUEST
    assert create_version_response.json() == {
        "environment": SEGMENT_OVERRIDE_LIMIT_EXCEEDED_MESSAGE
    }
    assert (
        EnvironmentFeatureVersion.objects.filter(
            environment=environment_v2_versioning, feature=feature
        ).count()
        == 2
    )


def test_segment_override_limit_excludes_older_versions__when_not_creating_any_new_overrides(
    feature: Feature,
    segment: Segment,
    environment_v2_versioning: Environment,
    project: Project,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE])
    with_project_permissions([VIEW_PROJECT])

    # We update the limit of segment overrides on the project
    project.max_segment_overrides_allowed = 1
    project.save()

    # And we create an existing version with a segment override in it
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=version_2,
        feature_segment=FeatureSegment.objects.create(
            feature=feature,
            segment=segment,
            environment=environment_v2_versioning,
            environment_feature_version=version_2,
        ),
    )
    version_2.publish()

    data = {"publish_immediately": True}
    create_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    # When
    create_version_response = staff_client.post(
        create_version_url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert create_version_response.status_code == status.HTTP_201_CREATED

    version_3_uuid = create_version_response.json()["uuid"]
    assert FeatureState.objects.filter(
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version__uuid=version_3_uuid,
    ).exists()


def test_segment_override_limit_excludes_older_versions__when_creating_new_override(
    feature: Feature,
    segment: Segment,
    another_segment: Segment,
    environment_v2_versioning: Environment,
    project: Project,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE])
    with_project_permissions([VIEW_PROJECT])

    # We update the limit of segment overrides on the project
    project.max_segment_overrides_allowed = 2
    project.save()

    # And we create an existing version with a segment override in it
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=version_2,
        feature_segment=FeatureSegment.objects.create(
            feature=feature,
            segment=segment,
            environment=environment_v2_versioning,
            environment_feature_version=version_2,
        ),
    )
    version_2.publish()

    data = {
        "publish_immediately": True,
        "feature_states_to_create": [
            {
                "enabled": True,
                "feature_state_value": {
                    "type": "unicode",
                    "string_value": "some new value",
                },
                "feature_segment": {
                    "segment": another_segment.id,
                },
            }
        ],
    }

    create_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    # When
    create_version_response = staff_client.post(
        create_version_url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert create_version_response.status_code == status.HTTP_201_CREATED

    version_3_uuid = create_version_response.json()["uuid"]
    assert FeatureState.objects.filter(
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version__uuid=version_3_uuid,
    ).exists()


def test_segment_override_limit_excludes_overrides_being_deleted_when_creating_new_override(
    feature: Feature,
    segment: Segment,
    another_segment: Segment,
    environment_v2_versioning: Environment,
    project: Project,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE])
    with_project_permissions([VIEW_PROJECT])

    # We update the limit of segment overrides on the project
    project.max_segment_overrides_allowed = 1
    project.save()

    # And we create an existing version with a segment override in it
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=version_2,
        feature_segment=FeatureSegment.objects.create(
            feature=feature,
            segment=segment,
            environment=environment_v2_versioning,
            environment_feature_version=version_2,
        ),
    )
    version_2.publish()

    data = {
        "publish_immediately": True,
        "feature_states_to_create": [
            {
                "enabled": True,
                "feature_state_value": {
                    "type": "unicode",
                    "string_value": "some new value",
                },
                "feature_segment": {
                    "segment": another_segment.id,
                },
            }
        ],
        "segment_ids_to_delete_overrides": [segment.id],
    }

    create_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    # When
    create_version_response = staff_client.post(
        create_version_url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert create_version_response.status_code == status.HTTP_201_CREATED

    version_3_uuid = create_version_response.json()["uuid"]
    assert FeatureState.objects.filter(
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version__uuid=version_3_uuid,
    ).exists()


def test_cannot_create_new_version_for_environment_not_enabled_for_versioning_v2(
    environment: Environment,
    feature: Feature,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE])
    with_project_permissions([VIEW_PROJECT])

    url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment.id, feature.id],
    )

    # When
    response = staff_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert response.json() == {
        "environment": "Environment must use v2 feature versioning."
    }


@pytest.mark.freeze_time(now - timedelta(days=DEFAULT_VERSION_LIMIT_DAYS + 1))
@pytest.mark.parametrize(
    "plan_id, is_saas",
    (("free", True), ("free", False), ("startup", True), ("scale-up", True)),
)
def test_list_versions_only_returns_allowed_amount_for_non_enterprise_plan(
    feature: Feature,
    environment_v2_versioning: Environment,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
    subscription: Subscription,
    freezer: FrozenDateTimeFactory,
    plan_id: str,
    is_saas: bool,
    mocker: MockerFixture,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])
    with_project_permissions([VIEW_PROJECT])

    mocker.patch("organisations.models.is_saas", return_value=is_saas)

    url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    subscription.plan = plan_id
    subscription.save()

    # First, let's create some versions at the frozen time which is
    # outside the limit allowed when using a non-enterprise plan
    outside_limit_versions = []
    for _ in range(3):
        version = EnvironmentFeatureVersion.objects.create(
            environment=environment_v2_versioning, feature=feature
        )
        version.publish(staff_user)
        outside_limit_versions.append(version)

    # Now let's jump to the current time and create some versions which
    # are inside the limit when using a non-enterprise plan
    freezer.move_to(now)

    inside_limit_versions = []
    for _ in range(3):
        version = EnvironmentFeatureVersion.objects.create(
            environment=environment_v2_versioning, feature=feature
        )
        version.publish(staff_user)
        inside_limit_versions.append(version)

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3
    assert {v["uuid"] for v in response_json["results"]} == {
        str(v.uuid) for v in inside_limit_versions
    }


@pytest.mark.freeze_time(now - timedelta(days=DEFAULT_VERSION_LIMIT_DAYS + 1))
def test_list_versions_always_returns_current_version_even_if_outside_limit(
    feature: Feature,
    environment_v2_versioning: Environment,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
    subscription: Subscription,
    freezer: FrozenDateTimeFactory,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])
    with_project_permissions([VIEW_PROJECT])

    url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    assert subscription.subscription_plan_family == SubscriptionPlanFamily.FREE

    # First, let's create a new version, after the initial version, but
    # still outside the limit allowed when using a non-enterprise plan
    freezer.move_to(timezone.now() + timedelta(minutes=5))
    latest_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    latest_version.publish(staff_user)

    # When
    # we jump to the current time and retrieve the versions
    freezer.move_to(now)
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["uuid"] == str(latest_version.uuid)


@pytest.mark.freeze_time(now - timedelta(days=DEFAULT_VERSION_LIMIT_DAYS + 1))
def test_list_versions_returns_all_versions_for_enterprise_plan_when_saas(
    feature: Feature,
    environment_v2_versioning: Environment,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_project_permissions: WithProjectPermissionsCallable,
    subscription: Subscription,
    freezer: FrozenDateTimeFactory,
    mocker: MockerFixture,
) -> None:
    # Given
    is_saas = True
    with_environment_permissions([VIEW_ENVIRONMENT])
    with_project_permissions([VIEW_PROJECT])

    url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning.id, feature.id],
    )

    mocker.patch("organisations.models.is_saas", return_value=is_saas)
    mocker.patch("organisations.models.is_enterprise", return_value=not is_saas)

    # Let's set the subscription plan as start up
    subscription.plan = "enterprise"
    subscription.save()

    OrganisationSubscriptionInformationCache.objects.update_or_create(
        organisation=subscription.organisation,
        defaults={"feature_history_visibility_days": None},
    )

    initial_version = EnvironmentFeatureVersion.objects.get(
        feature=feature, environment=environment_v2_versioning
    )

    # First, let's create some versions at the frozen time which is
    # outside the limit allowed when using the scale up plan (but
    # shouldn't matter to the enterprise plan.
    all_versions = []
    for _ in range(3):
        version = EnvironmentFeatureVersion.objects.create(
            environment=environment_v2_versioning, feature=feature
        )
        version.publish(staff_user)
        all_versions.append(version)

    # Now let's jump to the current time and create some versions which
    # are inside the limit when using the startup plan
    freezer.move_to(now)

    for _ in range(3):
        version = EnvironmentFeatureVersion.objects.create(
            environment=environment_v2_versioning, feature=feature
        )
        version.publish(staff_user)
        all_versions.append(version)

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 7  # we created 6, plus the original version
    assert {v["uuid"] for v in response_json["results"]} == {
        str(v.uuid) for v in [initial_version, *all_versions]
    }
