"""https://docs.flagsmith.com/managing-flags/updating-flags"""

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.dataclasses import AuthorData
from environments.models import Environment
from features.future.exceptions import (
    DuplicatePriorityError,
    SegmentOverrideNotFoundError,
)
from features.future.services import delete_segment_override, get_flag, update_flag
from features.future.types import UpdateFlagRequest
from features.models import Feature
from features.versioning.models import VersionChangeSet
from features.versioning.serializers import (
    EnvironmentFeatureVersionCreateSerializer,
)
from features.versioning.tasks import enable_v2_versioning
from features.workflows.core.models import ChangeRequest
from projects.models import Project
from segments.models import Segment
from users.models import FFAdminUser


@pytest.fixture()
def v2_environment(environment: Environment, feature: Feature) -> Environment:
    # Versions are created for the flags that exist, so the feature comes first.
    enable_v2_versioning(environment_id=environment.id)
    v2: Environment = Environment.objects.get(id=environment.id)
    return v2


@pytest.fixture()
def staging_change_request(
    v2_environment: Environment, admin_user: FFAdminUser
) -> ChangeRequest:
    change_request: ChangeRequest = ChangeRequest.objects.create(
        environment=v2_environment, title="Test CR", user_id=admin_user.id
    )
    return change_request


@pytest.fixture()
def other_segment(project: Project) -> Segment:
    other: Segment = Segment.objects.create(project=project, name="Other segment")
    return other


def _update(
    *,
    environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
    changes: UpdateFlagRequest,
    change_request: ChangeRequest | None = None,
    replace: bool = False,
) -> None:
    update_flag(
        environment=environment,
        feature=feature,
        changes=changes,
        replace=replace,
        author=AuthorData(user=admin_user),
        change_request=change_request,
        overwrite_system_segment_overrides=False,
    )


def _get_change_set(
    change_request: ChangeRequest, feature: Feature
) -> VersionChangeSet:
    change_set: VersionChangeSet = VersionChangeSet.objects.get(
        change_request=change_request, feature=feature
    )
    return change_set


def test_update_flag__no_change_request__updates_live_flag(
    v2_environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given
    changes: UpdateFlagRequest = {"environment_default": {"enabled": True}}

    # When
    _update(
        environment=v2_environment,
        feature=feature,
        admin_user=admin_user,
        changes=changes,
    )

    # Then
    assert get_flag(environment=v2_environment, feature=feature)["environment_default"][
        "enabled"
    ]
    assert not VersionChangeSet.objects.filter(feature=feature).exists()


def test_update_flag__change_request_environment_default__stages_change_without_changing_live_flag(
    v2_environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
    staging_change_request: ChangeRequest,
) -> None:
    # Given
    changes: UpdateFlagRequest = {"environment_default": {"enabled": True}}

    # When
    _update(
        environment=v2_environment,
        feature=feature,
        admin_user=admin_user,
        changes=changes,
        change_request=staging_change_request,
    )

    # Then
    change_set = _get_change_set(staging_change_request, feature)
    [staged_default] = change_set.get_parsed_feature_states_to_update()
    assert staged_default["feature_segment"] is None
    assert staged_default["enabled"] is True
    assert change_set.get_parsed_feature_states_to_create() == []
    assert change_set.get_parsed_segment_ids_to_delete_overrides() == []
    assert not get_flag(environment=v2_environment, feature=feature)[
        "environment_default"
    ]["enabled"]


def test_update_flag__change_request_new_segment_override__stages_creation_at_given_priority(
    v2_environment: Environment,
    feature: Feature,
    segment: Segment,
    admin_user: FFAdminUser,
    staging_change_request: ChangeRequest,
) -> None:
    # Given
    changes: UpdateFlagRequest = {
        "segment_overrides": [
            {"segment": {"id": segment.id}, "priority": 3, "enabled": True}
        ]
    }

    # When
    _update(
        environment=v2_environment,
        feature=feature,
        admin_user=admin_user,
        changes=changes,
        change_request=staging_change_request,
    )

    # Then
    [staged_override] = _get_change_set(
        staging_change_request, feature
    ).get_parsed_feature_states_to_create()
    assert staged_override["feature_segment"] == {"segment": segment.id, "priority": 3}
    assert staged_override["enabled"] is True
    assert (
        get_flag(environment=v2_environment, feature=feature)["segment_overrides"] == []
    )


def test_update_flag__change_request_with_several_changes__stages_them_in_one_change_set(
    v2_environment: Environment,
    feature: Feature,
    segment: Segment,
    other_segment: Segment,
    admin_user: FFAdminUser,
    staging_change_request: ChangeRequest,
) -> None:
    # Given a live override for one segment
    _update(
        environment=v2_environment,
        feature=feature,
        admin_user=admin_user,
        changes={
            "segment_overrides": [{"segment": {"id": segment.id}, "enabled": False}]
        },
    )

    # When an environment default change, an update and a creation are staged together
    changes: UpdateFlagRequest = {
        "environment_default": {"enabled": True},
        "segment_overrides": [
            {"segment": {"id": segment.id}, "enabled": True},
            {"segment": {"id": other_segment.id}, "priority": 1},
        ],
    }
    _update(
        environment=v2_environment,
        feature=feature,
        admin_user=admin_user,
        changes=changes,
        change_request=staging_change_request,
    )

    # Then all of them land in the same change set
    assert (
        VersionChangeSet.objects.filter(change_request=staging_change_request).count()
        == 1
    )
    change_set = _get_change_set(staging_change_request, feature)
    default_update, override_update = change_set.get_parsed_feature_states_to_update()
    assert default_update["feature_segment"] is None
    assert default_update["enabled"] is True
    assert override_update["feature_segment"]["segment"] == segment.id
    assert override_update["enabled"] is True
    [override_creation] = change_set.get_parsed_feature_states_to_create()
    assert override_creation["feature_segment"] == {
        "segment": other_segment.id,
        "priority": 1,
    }

    # And the live flag is untouched
    live = get_flag(environment=v2_environment, feature=feature)
    assert live["environment_default"]["enabled"] is False
    [live_override] = live["segment_overrides"]
    assert live_override["enabled"] is False


def test_update_flag__change_request_staged_twice__merges_into_one_entry(
    v2_environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
    staging_change_request: ChangeRequest,
) -> None:
    # Given a staged change to the environment default
    _update(
        environment=v2_environment,
        feature=feature,
        admin_user=admin_user,
        changes={"environment_default": {"enabled": True}},
        change_request=staging_change_request,
    )

    # When a later change stages only the value
    _update(
        environment=v2_environment,
        feature=feature,
        admin_user=admin_user,
        changes={
            "environment_default": {"value": {"type": "string", "value": "staged"}}
        },
        change_request=staging_change_request,
    )

    # Then the earlier change is kept alongside the later one
    [staged_default] = _get_change_set(
        staging_change_request, feature
    ).get_parsed_feature_states_to_update()
    assert staged_default["enabled"] is True
    assert staged_default["feature_state_value"]["string_value"] == "staged"


def test_update_flag__change_request_replacing_overrides__stages_deletion_of_live_override(
    v2_environment: Environment,
    feature: Feature,
    segment: Segment,
    admin_user: FFAdminUser,
    staging_change_request: ChangeRequest,
) -> None:
    # Given a live override for the segment
    _update(
        environment=v2_environment,
        feature=feature,
        admin_user=admin_user,
        changes={"segment_overrides": [{"segment": {"id": segment.id}}]},
    )

    # When the flag is replaced without that override
    _update(
        environment=v2_environment,
        feature=feature,
        admin_user=admin_user,
        changes={"segment_overrides": []},
        change_request=staging_change_request,
        replace=True,
    )

    # Then its removal is staged, and the live override remains
    change_set = _get_change_set(staging_change_request, feature)
    assert change_set.get_parsed_segment_ids_to_delete_overrides() == [segment.id]
    assert (
        len(get_flag(environment=v2_environment, feature=feature)["segment_overrides"])
        == 1
    )


def test_update_flag__change_request_overrides_sharing_priority__raises_duplicate_priority_error(
    v2_environment: Environment,
    feature: Feature,
    segment: Segment,
    other_segment: Segment,
    admin_user: FFAdminUser,
    staging_change_request: ChangeRequest,
) -> None:
    # Given two overrides that would share a priority
    changes: UpdateFlagRequest = {
        "segment_overrides": [
            {"segment": {"id": segment.id}, "priority": 2},
            {"segment": {"id": other_segment.id}, "priority": 2},
        ]
    }

    # When / Then the change is refused and nothing is staged
    with pytest.raises(DuplicatePriorityError):
        _update(
            environment=v2_environment,
            feature=feature,
            admin_user=admin_user,
            changes=changes,
            change_request=staging_change_request,
        )
    assert not VersionChangeSet.objects.filter(
        change_request=staging_change_request
    ).exists()


def test_update_flag__staged_payloads__are_accepted_by_publishing_serializer(
    v2_environment: Environment,
    feature: Feature,
    segment: Segment,
    admin_user: FFAdminUser,
    staging_change_request: ChangeRequest,
) -> None:
    # Given changes staged as a change request
    _update(
        environment=v2_environment,
        feature=feature,
        admin_user=admin_user,
        changes={
            "environment_default": {"enabled": True},
            "segment_overrides": [{"segment": {"id": segment.id}, "priority": 0}],
        },
        change_request=staging_change_request,
    )
    change_set = _get_change_set(staging_change_request, feature)

    # When the staged payloads are given to the serializer that publishes them
    serializer = EnvironmentFeatureVersionCreateSerializer(
        data={
            "feature_states_to_create": change_set.get_parsed_feature_states_to_create(),
            "feature_states_to_update": change_set.get_parsed_feature_states_to_update(),
            "segment_ids_to_delete_overrides": (
                change_set.get_parsed_segment_ids_to_delete_overrides()
            ),
        }
    )

    # Then they are valid
    assert serializer.is_valid(), serializer.errors


def test_update_flag__change_request_from_another_environment__raises_validation_error(
    v2_environment: Environment,
    feature: Feature,
    project: Project,
    admin_user: FFAdminUser,
) -> None:
    # Given a change request for a different environment
    other_environment = Environment.objects.create(name="Other", project=project)
    other_change_request = ChangeRequest.objects.create(
        environment=other_environment, title="Other CR", user_id=admin_user.id
    )

    # When / Then the change is refused and nothing is staged
    with pytest.raises(ValidationError):
        _update(
            environment=v2_environment,
            feature=feature,
            admin_user=admin_user,
            changes={"environment_default": {"enabled": True}},
            change_request=other_change_request,
        )
    assert not VersionChangeSet.objects.filter(
        change_request=other_change_request
    ).exists()


def test_update_flag__committed_change_request__raises_validation_error(
    v2_environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
    staging_change_request: ChangeRequest,
) -> None:
    # Given a change request that has been committed
    staging_change_request.committed_at = timezone.now()

    # When / Then the change is refused
    with pytest.raises(ValidationError):
        _update(
            environment=v2_environment,
            feature=feature,
            admin_user=admin_user,
            changes={"environment_default": {"enabled": True}},
            change_request=staging_change_request,
        )
    assert not VersionChangeSet.objects.filter(
        change_request=staging_change_request
    ).exists()


def test_update_flag__change_request_in_v1_versioned_environment__raises_validation_error(
    environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given an environment that does not use v2 versioning, and a change request for it
    change_request = ChangeRequest.objects.create(
        environment=environment, title="V1 CR", user_id=admin_user.id
    )

    # When / Then the change is refused, since change sets publish through v2 versions
    with pytest.raises(ValidationError):
        _update(
            environment=environment,
            feature=feature,
            admin_user=admin_user,
            changes={"environment_default": {"enabled": True}},
            change_request=change_request,
        )


def test_delete_segment_override__change_request__stages_deletion_without_changing_live_flag(
    v2_environment: Environment,
    feature: Feature,
    segment: Segment,
    admin_user: FFAdminUser,
    staging_change_request: ChangeRequest,
) -> None:
    # Given a live override for the segment
    _update(
        environment=v2_environment,
        feature=feature,
        admin_user=admin_user,
        changes={"segment_overrides": [{"segment": {"id": segment.id}}]},
    )

    # When its deletion is staged
    delete_segment_override(
        environment=v2_environment,
        feature=feature,
        segment_id=segment.id,
        author=AuthorData(user=admin_user),
        change_request=staging_change_request,
        overwrite_system_segment_overrides=False,
    )

    # Then the deletion is staged and the live override remains
    change_set = _get_change_set(staging_change_request, feature)
    assert change_set.get_parsed_segment_ids_to_delete_overrides() == [segment.id]
    assert (
        len(get_flag(environment=v2_environment, feature=feature)["segment_overrides"])
        == 1
    )


def test_delete_segment_override__change_request_without_override__raises_not_found(
    v2_environment: Environment,
    feature: Feature,
    other_segment: Segment,
    admin_user: FFAdminUser,
    staging_change_request: ChangeRequest,
) -> None:
    # Given no override for the segment
    # When / Then its deletion is refused
    with pytest.raises(SegmentOverrideNotFoundError):
        delete_segment_override(
            environment=v2_environment,
            feature=feature,
            segment_id=other_segment.id,
            author=AuthorData(user=admin_user),
            change_request=staging_change_request,
            overwrite_system_segment_overrides=False,
        )
