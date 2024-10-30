import json
from datetime import timedelta

import pytest
from core.constants import STRING
from django.utils import timezone
from freezegun import freeze_time
from pytest_mock import MockerFixture

from environments.models import Environment
from environments.tasks import rebuild_environment_document
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.exceptions import FeatureVersioningError
from features.versioning.models import (
    EnvironmentFeatureVersion,
    VersionChangeSet,
)
from features.workflows.core.models import ChangeRequest
from projects.models import Project
from segments.models import Segment
from users.models import FFAdminUser

now = timezone.now()


def test_create_new_environment_feature_version_clones_feature_states_from_previous_version(
    environment_v2_versioning, feature
):
    # Given
    original_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )

    segment = Segment.objects.create(project=environment_v2_versioning.project)
    feature_segment = FeatureSegment.objects.create(
        segment=segment, feature=feature, environment=environment_v2_versioning
    )
    FeatureState.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        feature_segment=feature_segment,
        environment_feature_version=original_version,
    )

    # When
    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # Then
    # the version is given a uuid
    assert new_version.uuid

    # and the correct feature states are cloned and added to the new version
    assert new_version.feature_states.count() == 2
    assert new_version.feature_states.filter(
        environment=environment_v2_versioning,
        feature=feature,
        feature_segment=None,
        identity=None,
    ).exists()
    assert new_version.feature_states.filter(
        environment=environment_v2_versioning,
        feature=feature,
        feature_segment__segment=segment,
        identity=None,
    ).exists()

    # but the existing feature states are left untouched
    assert (
        FeatureState.objects.filter(
            environment_feature_version=original_version
        ).count()
        == 2
    )


def test_environment_feature_version_create_initial_version_fails_for_v1_versioning_environment(
    feature: "Feature", project: "Project"
) -> None:
    # Given
    environment = Environment.objects.create(
        name="Test", project=project, use_v2_feature_versioning=False
    )

    # When
    with pytest.raises(FeatureVersioningError) as e:
        EnvironmentFeatureVersion.create_initial_version(
            environment=environment, feature=feature
        )

    # Then
    assert (
        "Cannot create initial version for environment using v1 versioning"
        in e.exconly()
    )


def test_environment_feature_version_create_initial_version_fails_if_version_already_exists(
    feature: "Feature", project: "Project"
) -> None:
    # Given
    # Initial version is created as part of the hooks on the environment model
    environment = Environment.objects.create(
        name="Test", project=project, use_v2_feature_versioning=True
    )
    assert EnvironmentFeatureVersion.objects.filter(
        environment=environment, feature=feature
    )

    # When
    with pytest.raises(FeatureVersioningError) as e:
        EnvironmentFeatureVersion.create_initial_version(
            environment=environment, feature=feature
        )

    # Then
    assert (
        "Version already exists for this feature / environment combination."
        in e.exconly()
    )


def test_get_previous_version(feature: "Feature", project: "Project") -> None:
    # Given
    environment = Environment.objects.create(
        name="Test", project=project, use_v2_feature_versioning=True
    )

    version_1 = EnvironmentFeatureVersion.objects.get(
        environment=environment, feature=feature
    )
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )

    # Then
    assert version_2.get_previous_version() == version_1


def test_get_previous_version_ignores_unpublished_version(
    feature: "Feature", project: "Project"
) -> None:
    # Given
    environment = Environment.objects.create(
        name="Test", project=project, use_v2_feature_versioning=True
    )

    version_1 = EnvironmentFeatureVersion.objects.get(
        environment=environment, feature=feature
    )
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )
    version_3 = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )

    # Then
    assert version_2.is_live is False
    assert version_3.get_previous_version() == version_1


def test_get_previous_version_returns_previous_version_if_there_is_a_more_recent_previous_version(
    feature: "Feature",
    environment_v2_versioning: Environment,
    admin_user: "FFAdminUser",
) -> None:
    # Given
    # The initial version created when enabling versioning_v2
    version_0 = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )

    # Now, let's create (and publish) 2 new versions
    version_1 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    version_1.publish(admin_user)
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    version_2.publish(admin_user)

    # When
    previous_version = version_1.get_previous_version()

    # Then
    # The previous version for the first version we created should be the
    # original version created when enabling versioning_v2
    assert previous_version == version_0


def test_publish(
    feature: "Feature",
    project: "Project",
    admin_user: "FFAdminUser",
    mocker: "MockerFixture",
) -> None:
    # Given
    environment = Environment.objects.create(
        name="Test", project=project, use_v2_feature_versioning=True
    )
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )

    mocked_rebuild_environment_document = mocker.patch(
        "features.versioning.receivers.rebuild_environment_document",
        autospec=rebuild_environment_document,
    )

    # When
    with freeze_time(now):
        version_2.publish(published_by=admin_user)

    # Then
    assert version_2.is_live
    assert version_2.live_from == now
    assert version_2.published is True
    assert version_2.published_by == admin_user

    mocked_rebuild_environment_document.delay.assert_called_once_with(
        kwargs={"environment_id": environment.id},
        delay_until=version_2.live_from,
    )


def test_update_version_webhooks_triggered_when_version_published(
    environment_v2_versioning: Environment,
    feature: "Feature",
    admin_user: "FFAdminUser",
    mocker: "MockerFixture",
) -> None:
    # Given
    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
    )

    mock_trigger_update_version_webhooks = mocker.patch(
        "features.versioning.receivers.trigger_update_version_webhooks"
    )

    # When
    new_version.publish(admin_user)

    # Then
    mock_trigger_update_version_webhooks.delay.assert_called_once_with(
        kwargs={"environment_feature_version_uuid": str(new_version.uuid)},
        delay_until=new_version.live_from,
    )


def test_get_latest_versions_does_not_return_versions_scheduled_for_the_future(
    environment_v2_versioning: Environment,
    feature: "Feature",
    admin_user: "FFAdminUser",
) -> None:
    # Given
    version_0 = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )

    # Let's create a version scheduled for the future, that we'll publish
    scheduled_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        live_from=timezone.now() + timedelta(hours=1),
    )
    scheduled_version.publish(admin_user)

    # When
    latest_versions = EnvironmentFeatureVersion.objects.get_latest_versions_as_queryset(
        environment_id=environment_v2_versioning.id
    )

    # Then
    assert latest_versions.count() == 1
    assert latest_versions.first() == version_0


def test_version_change_set_adds_environment_on_create_with_change_request(
    environment_v2_versioning: Environment,
    feature: "Feature",
    change_request: ChangeRequest,
) -> None:
    # Given
    version_change_set = VersionChangeSet(
        feature=feature, change_request=change_request
    )

    # When
    version_change_set.save()

    # Then
    assert version_change_set.environment == change_request.environment


def test_version_change_set_adds_environment_on_create_with_environment_feature_version(
    environment_v2_versioning: Environment, feature: "Feature"
) -> None:
    # Given
    version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    version_change_set = VersionChangeSet(
        feature=feature, environment_feature_version=version
    )

    # When
    version_change_set.save()

    # Then
    assert version_change_set.environment == version.environment


def test_version_change_set_create_fails_if_no_related_object(
    feature: "Feature",
) -> None:
    # Given
    version_change_set = VersionChangeSet(feature=feature)

    # When
    with pytest.raises(RuntimeError) as e:
        version_change_set.save()

    # Then
    assert (
        str(e.value)
        == "Version change set should belong to either a change request, or a version."
    )


def test_version_change_set_get_conflicts(
    project: Project,
    segment: Segment,
    another_segment: Segment,
    feature: "Feature",
    segment_featurestate: FeatureState,
    another_segment_featurestate: FeatureState,
    environment_v2_versioning: Environment,
    admin_user: "FFAdminUser",
) -> None:
    # Given
    # We create 4 change sets...
    # ... one to modify the environment default feature state
    change_request_1 = ChangeRequest.objects.create(
        environment=environment_v2_versioning, title="Test CR 1"
    )
    VersionChangeSet.objects.create(
        change_request=change_request_1,
        feature=feature,
        feature_states_to_update=json.dumps(
            [
                {
                    "feature_segment": None,
                    "enabled": True,
                    "feature_state_value": {
                        "type": STRING,
                        "string_value": "value from version change set 1",
                    },
                }
            ]
        ),
        feature_states_to_create="[]",
        segment_ids_to_delete_overrides="[]",
    )

    # ... one to create a new segment override for a new segment
    new_segment = Segment.objects.create(name="new segment", project=project)
    change_request_2 = ChangeRequest.objects.create(
        environment=environment_v2_versioning, title="Test CR 2"
    )
    VersionChangeSet.objects.create(
        change_request=change_request_2,
        feature=feature,
        feature_states_to_update="[]",
        feature_states_to_create=json.dumps(
            [
                {
                    "feature_segment": {"segment": new_segment.id},
                    "enabled": True,
                    "feature_state_value": {
                        "type": STRING,
                        "string_value": "segment override value from version change set 2",
                    },
                }
            ]
        ),
        segment_ids_to_delete_overrides="[]",
    )

    # ... and one to remove the segment override for the first segment
    change_request_3 = ChangeRequest.objects.create(
        environment=environment_v2_versioning, title="Test CR 3"
    )
    VersionChangeSet.objects.create(
        change_request=change_request_3,
        feature=feature,
        feature_states_to_update="[]",
        feature_states_to_create="[]",
        segment_ids_to_delete_overrides=json.dumps([segment.id]),
    )

    # ... and one to update the segment override for the second segment
    change_request_4 = ChangeRequest.objects.create(
        environment=environment_v2_versioning, title="Test CR 4"
    )
    VersionChangeSet.objects.create(
        change_request=change_request_4,
        feature=feature,
        feature_states_to_update=json.dumps(
            [
                {
                    "feature_segment": {"segment": another_segment.id},
                    "enabled": True,
                    "feature_state_value": {
                        "type": STRING,
                        "string_value": "segment override value from version change set 4",
                    },
                }
            ]
        ),
        feature_states_to_create="[]",
        segment_ids_to_delete_overrides="[]",
    )

    # Finally, we create another change set to modify all the same things as each individual
    # change set that we already defined above.
    primary_change_request = ChangeRequest.objects.create(
        environment=environment_v2_versioning, title="Test CR"
    )
    primary_version_change_set = VersionChangeSet.objects.create(
        change_request=primary_change_request,
        feature=feature,
        feature_states_to_update=json.dumps(
            [
                {
                    "feature_segment": None,
                    "enabled": True,
                    "feature_state_value": {
                        "type": STRING,
                        "string_value": "primary value",
                    },
                },
                {
                    "feature_segment": {"segment": another_segment.id},
                    "enabled": True,
                    "feature_state_value": {
                        "type": STRING,
                        "string_value": "segment override value from primary change set",
                    },
                },
            ]
        ),
        feature_states_to_create=json.dumps(
            [
                {
                    "feature_segment": {"segment": new_segment.id},
                    "enabled": True,
                    "feature_state_value": {
                        "type": STRING,
                        "string_value": "segment override value from primary change set",
                    },
                }
            ]
        ),
        segment_ids_to_delete_overrides=json.dumps([segment.id]),
    )

    # And we publish the first 4 change sets (via the change requests)
    for cr in [change_request_1, change_request_2, change_request_3, change_request_4]:
        cr.commit(admin_user)

    # When
    conflicts = primary_version_change_set.get_conflicts()

    # Then
    assert len(conflicts) == 4

    # build a dictionary keyed off the original_cr_id to make the
    # assertions below easier.
    conflict_dict = {c.original_cr_id: c for c in conflicts}

    assert conflict_dict[change_request_1.id].segment_id is None
    assert conflict_dict[change_request_1.id].is_environment_default

    assert conflict_dict[change_request_2.id].segment_id is new_segment.id
    assert not conflict_dict[change_request_2.id].is_environment_default

    assert conflict_dict[change_request_3.id].segment_id is segment.id
    assert not conflict_dict[change_request_3.id].is_environment_default

    assert conflict_dict[change_request_4.id].segment_id is another_segment.id
    assert not conflict_dict[change_request_4.id].is_environment_default


def test_version_change_set_publish_not_scheduled(
    environment_v2_versioning: Environment,
    change_request: ChangeRequest,
    feature: Feature,
    mocker: MockerFixture,
    admin_user: FFAdminUser,
) -> None:
    # Given
    mock_publish_version_change_set = mocker.patch(
        "features.versioning.tasks.publish_version_change_set"
    )

    version_change_set = VersionChangeSet.objects.create(
        change_request=change_request,
        feature=feature,
    )

    # When
    version_change_set.publish(admin_user)

    # Then
    mock_publish_version_change_set.assert_called_once_with(
        version_change_set_id=version_change_set.id, user_id=admin_user.id
    )


def test_version_change_set_publish_scheduled(
    environment_v2_versioning: Environment,
    change_request: ChangeRequest,
    feature: Feature,
    mocker: MockerFixture,
    admin_user: FFAdminUser,
) -> None:
    # Given
    mock_publish_version_change_set = mocker.patch(
        "features.versioning.tasks.publish_version_change_set"
    )

    live_from = timezone.now() + timedelta(days=1)
    version_change_set = VersionChangeSet.objects.create(
        change_request=change_request,
        feature=feature,
        live_from=live_from,
    )

    # When
    version_change_set.publish(admin_user)

    # Then
    mock_publish_version_change_set.delay.assert_called_once_with(
        kwargs={
            "version_change_set_id": version_change_set.id,
            "user_id": admin_user.id,
            "is_scheduled": True,
        },
        delay_until=live_from,
    )


def test_version_change_set_get_conflicts_returns_empty_list_if_published(
    feature: Feature,
    admin_user: FFAdminUser,
    segment: Segment,
    segment_featurestate: FeatureState,
    environment_v2_versioning: Environment,
) -> None:
    # Given
    # We create 2 change requests (with change sets) that operate on the
    # same segment override and publish them both
    change_sets = []
    for i in range(1, 3):
        change_set = VersionChangeSet.objects.create(
            change_request=ChangeRequest.objects.create(
                title=f"CR{i}",
                environment=environment_v2_versioning,
            ),
            feature=feature,
            feature_states_to_update=json.dumps(
                [
                    {
                        "feature_segment": {"segment": segment.id},
                        "enabled": True,
                        "feature_state_value": {
                            "type": STRING,
                            "string_value": f"override value {i}",
                        },
                    }
                ]
            ),
        )
        change_set.change_request.commit(admin_user)
        change_set.refresh_from_db()
        change_sets.append(change_set)

    # Then
    assert all(cs.get_conflicts() == [] for cs in change_sets)


def test_version_change_set_get_conflicts_returns_empty_list_if_no_conflicts(
    change_request: ChangeRequest,
    feature: Feature,
    segment: Segment,
    admin_user: FFAdminUser,
    environment_v2_versioning: Environment,
) -> None:
    # Given
    # We create 2 change requests (with change sets) that operate on different
    # elements of a given feature (one creates a segment override, one
    # updates the environment default)
    segment_override_change_set = VersionChangeSet.objects.create(
        change_request=ChangeRequest.objects.create(
            title="Segment Override CR",
            environment=environment_v2_versioning,
        ),
        feature=feature,
        feature_states_to_create=json.dumps(
            [
                {
                    "feature_segment": {"segment": segment.id},
                    "enabled": True,
                    "feature_state_value": {
                        "type": STRING,
                        "string_value": "override value",
                    },
                }
            ]
        ),
    )

    environment_default_change_set = VersionChangeSet.objects.create(
        change_request=ChangeRequest.objects.create(
            title="Segment Override CR",
            environment=environment_v2_versioning,
        ),
        feature=feature,
        feature_states_to_update=json.dumps(
            [
                {
                    "feature_segment": None,
                    "enabled": True,
                    "feature_state_value": {
                        "type": STRING,
                        "string_value": "updated value",
                    },
                }
            ]
        ),
    )

    # And we publish the segment override change set
    segment_override_change_set.change_request.commit(admin_user)
    segment_override_change_set.refresh_from_db()

    # When
    conflicts = environment_default_change_set.get_conflicts()

    # Then
    assert conflicts == []


def test_version_change_set_get_conflicts_returns_empty_list_if_no_change_sets_since_creation(
    change_request: ChangeRequest,
    feature: Feature,
) -> None:
    # Given
    change_set = VersionChangeSet.objects.create(
        change_request=change_request,
        feature=feature,
        feature_states_to_update=json.dumps(
            [
                {
                    "feature_segment": None,
                    "enabled": True,
                    "feature_state_value": {
                        "type": STRING,
                        "string_value": "updated value",
                    },
                }
            ]
        ),
    )

    # When
    conflicts = change_set.get_conflicts()

    # Then
    assert conflicts == []
