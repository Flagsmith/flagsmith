from datetime import timedelta

import pytest
from django.utils import timezone

from audit.constants import (
    RELEASE_PIPELINE_CREATED_MESSAGE,
    RELEASE_PIPELINE_DELETED_MESSAGE,
)
from environments.models import Environment
from features.models import Feature
from features.release_pipelines.core.exceptions import InvalidPipelineStateError
from features.release_pipelines.core.models import (
    PhasedRolloutState,
    PipelineStage,
    ReleasePipeline,
    StageActionType,
)
from features.versioning.models import EnvironmentFeatureVersion
from segments.models import Segment
from users.models import FFAdminUser


def test_release_pipeline_publish_raises_error_if_pipeline_is_already_published(
    release_pipeline: ReleasePipeline, admin_user: FFAdminUser
) -> None:
    # Given - the pipeline is already published
    release_pipeline.publish(admin_user)

    # When / Then
    with pytest.raises(
        InvalidPipelineStateError, match="Pipeline is already published."
    ):
        release_pipeline.publish(admin_user)


def test_release_pipeline_get_first_stage_returns_none_if_pipeline_has_no_stages(
    release_pipeline: ReleasePipeline,
) -> None:
    # When
    first_stage = release_pipeline.get_first_stage()

    # Then
    assert first_stage is None


def test_release_pipeline_get_first_stage_returns_correct_stage(
    release_pipeline: ReleasePipeline, environment: Environment
) -> None:
    # Given
    for i in range(3):
        PipelineStage.objects.create(
            name=f"Stage {i}",
            pipeline=release_pipeline,
            environment=environment,
            order=i,
        )

    # When
    first_stage = release_pipeline.get_first_stage()

    # Then
    assert first_stage.order == 0  # type: ignore[union-attr]


def test_release_pipeline_get_last_stage_returns_none_if_pipeline_has_no_stages(
    release_pipeline: ReleasePipeline,
) -> None:
    # When
    last_stage = release_pipeline.get_last_stage()

    # Then
    assert last_stage is None


def test_release_pipeline_get_last_stage_returns_correct_stage(
    release_pipeline: ReleasePipeline, environment: Environment
) -> None:
    # Given
    for i in range(3):
        PipelineStage.objects.create(
            name=f"Stage {i}",
            pipeline=release_pipeline,
            environment=environment,
            order=i,
        )

    # When
    last_stage = release_pipeline.get_last_stage()

    # Then
    assert last_stage.order == 2  # type: ignore[union-attr]


def test_release_pipeline_get_next_stage(
    release_pipeline: ReleasePipeline, environment: Environment
) -> None:
    # Given
    stage1 = PipelineStage.objects.create(
        name="Stage 1",
        pipeline=release_pipeline,
        environment=environment,
        order=0,
    )
    stage2 = PipelineStage.objects.create(
        name="Stage 2",
        pipeline=release_pipeline,
        environment=environment,
        order=1,
    )
    stage3 = PipelineStage.objects.create(
        name="Stage 3",
        pipeline=release_pipeline,
        environment=environment,
        order=2,
    )

    # Then
    assert stage1.get_next_stage() == stage2
    assert stage2.get_next_stage() == stage3
    assert stage3.get_next_stage() is None


def test_release_pipeline_get_create_log_message(
    release_pipeline: ReleasePipeline,
) -> None:
    # When
    expected_message = RELEASE_PIPELINE_CREATED_MESSAGE % release_pipeline.name

    # Then
    assert release_pipeline.get_create_log_message(release_pipeline) == expected_message


def test_release_pipeline_get_delete_log_message(
    release_pipeline: ReleasePipeline,
) -> None:
    # When
    expected_message = RELEASE_PIPELINE_DELETED_MESSAGE % release_pipeline.name

    # Then
    assert release_pipeline.get_delete_log_message(release_pipeline) == expected_message


def test_release_pipeline_unpublish(
    release_pipeline: ReleasePipeline, admin_user: FFAdminUser
) -> None:
    # Given - the pipeline is already published
    release_pipeline.publish(admin_user)

    # When
    release_pipeline.unpublish()

    # Then
    assert release_pipeline.published_at is None
    assert release_pipeline.published_by is None


def test_should_raise_error_when_unpublishing_unpublished_pipeline(
    release_pipeline: ReleasePipeline, admin_user: FFAdminUser
) -> None:
    # When/ Then
    with pytest.raises(InvalidPipelineStateError, match="Pipeline is not published."):
        release_pipeline.unpublish()


def test_release_pipeline_has_feature_in_flight(
    release_pipeline: ReleasePipeline,
    environment: Environment,
    pipeline_stage_enable_feature_on_enter: PipelineStage,
    admin_user: FFAdminUser,
    feature: Feature,
) -> None:
    # Given an unpublished environment feature version
    environment_version = EnvironmentFeatureVersion.objects.create(
        feature=feature,
        environment=environment,
        pipeline_stage=pipeline_stage_enable_feature_on_enter,
        published_at=None,
    )

    # Then
    assert release_pipeline.has_feature_in_flight() is True

    # Next, publish the environment feature version
    environment_version.published_at = timezone.now()
    environment_version.published_by = admin_user
    environment_version.save()

    # Then
    assert release_pipeline.has_feature_in_flight() is False


def test_phased_rollout_state_increase_split_does_not_exceed_100(
    phased_rollout_state: PhasedRolloutState,
) -> None:
    # Given
    initial_split = phased_rollout_state.initial_split
    increase_by = 50
    phased_rollout_state.increase_by = increase_by
    phased_rollout_state.save()

    # When
    phased_rollout_state.increase_split()
    # Then
    assert phased_rollout_state.current_split == initial_split + increase_by
    assert (
        phased_rollout_state.rollout_segment.rules.first().conditions.first().value  # type: ignore[union-attr]
        == str(phased_rollout_state.current_split)
    )

    # Next, increase the split again
    phased_rollout_state.increase_split()

    # Then - the split did not exceed 100
    assert phased_rollout_state.current_split == 100
    assert (
        phased_rollout_state.rollout_segment.rules.first().conditions.first().value  # type: ignore[union-attr]
        == str(100.0)
    )


def test_phased_rollout_complete_rollout(
    phased_rollout_state: PhasedRolloutState,
    rollout_segment: Segment,
) -> None:
    # When
    phased_rollout_state.complete_rollout()
    # Then
    assert phased_rollout_state.is_rollout_complete is True
    assert Segment.objects.filter(id=rollout_segment.id).exists() is False


def test_get_phased_rollout_action_returns_none_if_no_phased_rollout_action(
    pipeline_stage_enable_feature_on_enter: PipelineStage,
) -> None:
    # When
    phased_rollout_action = (
        pipeline_stage_enable_feature_on_enter.get_phased_rollout_action()
    )

    # Then
    assert phased_rollout_action is None


def test_get_phased_rollout_action_returns_phased_rollout_action_if_exists(
    pipeline_stage_phased_rollout: PipelineStage,
) -> None:
    # When
    phased_rollout_action = pipeline_stage_phased_rollout.get_phased_rollout_action()

    # Then
    assert phased_rollout_action is not None
    assert phased_rollout_action.action_type == StageActionType.PHASED_ROLLOUT.value


def test_pipeline_stage_on_enter_get_completed_feature_versions_qs(
    pipeline_stage_enable_feature_on_enter: PipelineStage,
    feature_in_pipeline_stage_enable_feature_on_enter: Feature,
    feature_completed_pipeline_phased_rollout: Feature,
    feature_in_pipeline_stage_phased_rollout: Feature,
    feature_in_pipeline_stage_update_feature_value_on_wait_for: Feature,
) -> None:
    # When
    completed_feature_versions = (
        pipeline_stage_enable_feature_on_enter.get_completed_feature_versions_qs()
    )

    # Then
    assert completed_feature_versions.count() == 0
    # Next, publish the feature in the pipeline stage
    feature_in_pipeline_stage_enable_feature_on_enter.environmentfeatureversion_set.filter(
        pipeline_stage=pipeline_stage_enable_feature_on_enter
    ).update(published_at=timezone.now())
    # Then
    assert completed_feature_versions.count() == 1
    assert (
        completed_feature_versions.first().feature  # type: ignore[union-attr]
        == feature_in_pipeline_stage_enable_feature_on_enter
    )


def test_pipeline_stage_on_enter_get_completed_feature_versions_qs_with_completed_after(
    pipeline_stage_enable_feature_on_enter: PipelineStage,
    feature_in_pipeline_stage_enable_feature_on_enter: Feature,
    feature_completed_pipeline_phased_rollout: Feature,
    feature_in_pipeline_stage_phased_rollout: Feature,
    feature_in_pipeline_stage_update_feature_value_on_wait_for: Feature,
) -> None:
    # Given - a feature completed 10 days ago
    ten_days_ago = timezone.now() - timedelta(days=10)
    nine_days_ago = timezone.now() - timedelta(days=9)
    feature_in_pipeline_stage_enable_feature_on_enter.environmentfeatureversion_set.filter(
        pipeline_stage=pipeline_stage_enable_feature_on_enter
    ).update(published_at=ten_days_ago)

    # When - we get feature completed 9 days ago
    completed_feature_versions = (
        pipeline_stage_enable_feature_on_enter.get_completed_feature_versions_qs(
            completed_after=nine_days_ago
        )
    )
    # Then - we don't get the feature completed 10 days ago
    assert completed_feature_versions.count() == 0
    # Next, let's get the features completed 10 days ago
    completed_feature_versions = (
        pipeline_stage_enable_feature_on_enter.get_completed_feature_versions_qs(
            completed_after=ten_days_ago
        )
    )
    # Then - we get the feature completed 10 days ago
    assert completed_feature_versions.count() == 1
    assert (
        completed_feature_versions.first().feature  # type: ignore[union-attr]
        == feature_in_pipeline_stage_enable_feature_on_enter
    )


def test_pipeline_stage_on_enter_get_in_stage_feature_versions_qs(
    pipeline_stage_enable_feature_on_enter: PipelineStage,
    feature_in_pipeline_stage_enable_feature_on_enter: Feature,
    feature_completed_pipeline_phased_rollout: Feature,
    feature_in_pipeline_stage_phased_rollout: Feature,
    feature_in_pipeline_stage_update_feature_value_on_wait_for: Feature,
) -> None:
    # When
    in_stage_feature_versions = (
        pipeline_stage_enable_feature_on_enter.get_in_stage_feature_versions_qs()
    )
    # Then
    assert in_stage_feature_versions.count() == 1
    assert (
        in_stage_feature_versions.first().feature  # type: ignore[union-attr]
        == feature_in_pipeline_stage_enable_feature_on_enter
    )
    # Next, publish the feature in the pipeline stage
    feature_in_pipeline_stage_enable_feature_on_enter.environmentfeatureversion_set.filter(
        pipeline_stage=pipeline_stage_enable_feature_on_enter
    ).update(published_at=timezone.now())
    # Then
    assert in_stage_feature_versions.count() == 0


def test_pipeline_stage_wait_for_get_completed_feature_versions_qs(
    pipeline_stage_update_feature_value_on_wait_for: PipelineStage,
    feature_in_pipeline_stage_update_feature_value_on_wait_for: Feature,
    feature_completed_pipeline_phased_rollout: Feature,
    feature_in_pipeline_stage_phased_rollout: Feature,
    feature_in_pipeline_stage_enable_feature_on_enter: Feature,
) -> None:
    # When
    completed_feature_versions = pipeline_stage_update_feature_value_on_wait_for.get_completed_feature_versions_qs()
    # Then
    assert completed_feature_versions.count() == 0
    # Next, publish the feature in the pipeline stage
    feature_in_pipeline_stage_update_feature_value_on_wait_for.environmentfeatureversion_set.filter(
        pipeline_stage=pipeline_stage_update_feature_value_on_wait_for
    ).update(published_at=timezone.now())
    # Then
    assert completed_feature_versions.count() == 1
    assert (
        completed_feature_versions.first().feature  # type: ignore[union-attr]
        == feature_in_pipeline_stage_update_feature_value_on_wait_for
    )


def test_pipeline_stage_wait_for_get_in_stage_feature_versions_qs(
    pipeline_stage_update_feature_value_on_wait_for: PipelineStage,
    feature_in_pipeline_stage_update_feature_value_on_wait_for: Feature,
    feature_completed_pipeline_phased_rollout: Feature,
    feature_in_pipeline_stage_phased_rollout: Feature,
    feature_in_pipeline_stage_enable_feature_on_enter: Feature,
) -> None:
    # When
    in_stage_feature_versions = pipeline_stage_update_feature_value_on_wait_for.get_in_stage_feature_versions_qs()
    # Then
    assert in_stage_feature_versions.count() == 1
    assert (
        in_stage_feature_versions.first().feature  # type: ignore[union-attr]
        == feature_in_pipeline_stage_update_feature_value_on_wait_for
    )
    # Next, publish the feature in the pipeline stage
    feature_in_pipeline_stage_update_feature_value_on_wait_for.environmentfeatureversion_set.filter(
        pipeline_stage=pipeline_stage_update_feature_value_on_wait_for
    ).update(published_at=timezone.now())
    # Then
    assert in_stage_feature_versions.count() == 0


def test_pipeline_stage_phased_rollout_get_completed_feature_versions_qs(
    pipeline_stage_phased_rollout: PipelineStage,
    feature_in_pipeline_stage_phased_rollout: Feature,
    feature_completed_pipeline_phased_rollout: Feature,
    feature_in_pipeline_stage_enable_feature_on_enter: Feature,
) -> None:
    # When
    completed_feature_versions = (
        pipeline_stage_phased_rollout.get_completed_feature_versions_qs()
    )
    # Then
    assert completed_feature_versions.count() == 1
    assert (
        completed_feature_versions.first().feature  # type: ignore[union-attr]
        == feature_completed_pipeline_phased_rollout
    )


def test_pipeline_stage_phased_rollout_get_completed_feature_versions_qs_with_completed_after(
    pipeline_stage_phased_rollout: PipelineStage,
    feature_in_pipeline_stage_phased_rollout: Feature,
    feature_completed_pipeline_phased_rollout: Feature,
    phased_rollout_state: PhasedRolloutState,
    feature_in_pipeline_stage_enable_feature_on_enter: Feature,
) -> None:
    # Given - a feature completed 10 days ago
    ten_days_ago = timezone.now() - timedelta(days=10)
    nine_days_ago = timezone.now() - timedelta(days=9)
    env_feature_version = (
        feature_completed_pipeline_phased_rollout.environmentfeatureversion_set.get(
            pipeline_stage=pipeline_stage_phased_rollout
        )
    )
    PhasedRolloutState.objects.filter(
        id=env_feature_version.phased_rollout_state.id  # type: ignore[union-attr]
    ).update(last_updated_at=ten_days_ago)

    # When - we get feature completed 9 days ago
    completed_feature_versions = (
        pipeline_stage_phased_rollout.get_completed_feature_versions_qs(
            completed_after=nine_days_ago
        )
    )
    # Then - we don't get the feature completed 10 days ago
    assert completed_feature_versions.count() == 0
    # Next, let's get the features completed 10 days ago
    completed_feature_versions = (
        pipeline_stage_phased_rollout.get_completed_feature_versions_qs(
            completed_after=ten_days_ago
        )
    )
    # Then - we get the feature completed 10 days ago
    assert completed_feature_versions.count() == 1
    assert (
        completed_feature_versions.first().feature  # type: ignore[union-attr]
        == feature_completed_pipeline_phased_rollout
    )


def test_pipeline_stage_phased_rollout_get_in_stage_feature_versions_qs(
    pipeline_stage_phased_rollout: PipelineStage,
    feature_in_pipeline_stage_phased_rollout: Feature,
    feature_completed_pipeline_phased_rollout: Feature,
    feature_in_pipeline_stage_enable_feature_on_enter: Feature,
) -> None:
    # When
    in_stage_feature_versions = (
        pipeline_stage_phased_rollout.get_in_stage_feature_versions_qs()
    )
    # Then
    assert in_stage_feature_versions.count() == 1
    assert (
        in_stage_feature_versions.first().feature  # type: ignore[union-attr]
        == feature_in_pipeline_stage_phased_rollout
    )


def test_release_pipeline_get_feature_versions_in_pipeline_qs(
    release_pipeline: ReleasePipeline,
    feature_in_pipeline_stage_enable_feature_on_enter: Feature,
    feature_in_pipeline_stage_phased_rollout: Feature,
    feature_in_pipeline_stage_update_feature_value_on_wait_for: Feature,
    feature_completed_pipeline_phased_rollout: Feature,
) -> None:
    # When
    feature_versions_in_pipeline = (
        release_pipeline.get_feature_versions_in_pipeline_qs()
    )
    # Then
    assert feature_versions_in_pipeline.count() == 3
    assert (
        feature_versions_in_pipeline.filter(
            feature=feature_in_pipeline_stage_enable_feature_on_enter
        ).exists()
        is True
    )
    assert (
        feature_versions_in_pipeline.filter(
            feature=feature_in_pipeline_stage_phased_rollout
        ).exists()
        is True
    )
    assert (
        feature_versions_in_pipeline.filter(
            feature=feature_in_pipeline_stage_update_feature_value_on_wait_for
        ).exists()
        is True
    )
