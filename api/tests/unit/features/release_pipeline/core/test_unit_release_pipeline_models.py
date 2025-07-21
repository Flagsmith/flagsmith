import pytest
from django.utils import timezone

from audit.constants import (
    RELEASE_PIPELINE_CREATED_MESSAGE,
    RELEASE_PIPELINE_DELETED_MESSAGE,
)
from environments.models import Environment
from features.models import EnvironmentFeatureVersion, Feature
from features.release_pipelines.core.exceptions import InvalidPipelineStateError
from features.release_pipelines.core.models import (
    PipelineStage,
    PipelineStageAction,
    PipelineStageTrigger,
    ReleasePipeline,
    StageActionType,
    StageTriggerType,
)
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


def test_clone_release_pipeline(
    release_pipeline: ReleasePipeline,
    environment: Environment,
    admin_user: FFAdminUser,
    segment: Segment,
) -> None:
    # Given - A release pipeline that is published
    release_pipeline.publish(admin_user)

    # with two stages, each with a wait trigger and two actions
    for i in range(2):
        pipeline_stage = PipelineStage.objects.create(
            name=f"Stage {i}",
            pipeline=release_pipeline,
            environment=environment,
            order=i,
        )
        PipelineStageTrigger.objects.create(
            trigger_type=StageTriggerType.WAIT_FOR.value,
            stage=pipeline_stage,
            trigger_body={"wait_for": "00:00:01"},
        )
        PipelineStageAction.objects.create(
            action_type=StageActionType.UPDATE_FEATURE_VALUE.value,
            action_body={"string_value": "stage_one_value", "type": "unicode"},
            stage=pipeline_stage,
        )
        PipelineStageAction.objects.create(
            action_type=StageActionType.UPDATE_FEATURE_VALUE_FOR_SEGMENT.value,
            action_body={
                "string_value": "stage_one_segment_override",
                "type": "unicode",
                "segment_id": segment.id,
            },
            stage=pipeline_stage,
        )
    # When
    cloned_pipeline = release_pipeline.clone()

    # Then
    # make sure the old pipeline is not modified
    release_pipeline.refresh_from_db()
    assert release_pipeline.published_at is not None
    assert release_pipeline.published_by is not None
    assert release_pipeline.stages.count() == 2

    # Assertions for the cloned pipeline
    assert cloned_pipeline.name == release_pipeline.name
    assert cloned_pipeline.project == release_pipeline.project
    assert cloned_pipeline.stages.count() == 2
    assert cloned_pipeline.published_at is None
    assert cloned_pipeline.published_by is None
    assert cloned_pipeline.id != release_pipeline.id
    assert cloned_pipeline.uuid != release_pipeline.uuid

    # Assertions for stages in the cloned pipeline
    assert cloned_pipeline.stages.count() == release_pipeline.stages.count()
    source_stages = list(release_pipeline.stages.all().order_by("order"))
    cloned_stages = list(cloned_pipeline.stages.all().order_by("order"))

    for i, source_stage in enumerate(source_stages):
        cloned_stage = cloned_stages[i]

        assert cloned_stage.id != source_stage.id  # Ensure it's a new object
        assert cloned_stage.name == source_stage.name
        assert cloned_stage.order == source_stage.order
        assert cloned_stage.environment == source_stage.environment
        assert (
            cloned_stage.pipeline == cloned_pipeline
        )  # Ensure it points to the new pipeline

        # source stage still points to the original pipeline
        assert source_stage.pipeline == release_pipeline

        # Assertions for trigger in the cloned stage
        source_trigger = source_stage.trigger
        cloned_trigger = cloned_stage.trigger

        assert cloned_trigger.id != source_trigger.id  # Ensure it's a new object
        assert cloned_trigger.trigger_type == source_trigger.trigger_type
        assert cloned_trigger.trigger_body == source_trigger.trigger_body
        assert cloned_trigger.stage == cloned_stage  # Ensure it points to the new stage

        # source trigger still points to the original stage
        assert source_trigger.stage == source_stage

        # Assertions for actions in the cloned stage
        source_actions = list(source_stage.actions.all())
        cloned_actions = list(cloned_stage.actions.all())

        assert len(cloned_actions) == len(source_actions)

        for j, source_action in enumerate(source_actions):
            cloned_action = cloned_actions[j]
            assert cloned_action.id != source_action.id  # Ensure it's a new object
            assert cloned_action.action_type == source_action.action_type
            assert cloned_action.action_body == source_action.action_body
            assert (
                cloned_action.stage == cloned_stage
            )  # Ensure it points to the new stage

            # source action still points to the original stage
            assert source_action.stage == source_stage


def test_release_pipeline_has_feature_in_flight(
    release_pipeline: ReleasePipeline,
    environment: Environment,
    pipeline_stage_enable_feature_on_enter: PipelineStage,
    admin_user: FFAdminUser,
    feature: Feature,
) -> None:
    # Given an unpublished environment feature version
    feature = release_pipeline.project.features.first()
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
