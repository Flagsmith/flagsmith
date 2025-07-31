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
    release_pipeline.unpublish(admin_user)

    # Then
    assert release_pipeline.published_at is None
    assert release_pipeline.published_by is None


def test_should_raise_error_when_unpublishing_unpublished_pipeline(
    release_pipeline: ReleasePipeline, admin_user: FFAdminUser
) -> None:
    # When/ Then
    with pytest.raises(InvalidPipelineStateError, match="Pipeline is not published."):
        release_pipeline.unpublish(admin_user)


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
