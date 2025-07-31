from datetime import timedelta

import pytest
from flag_engine.segments import constants

from environments.models import Environment
from features.release_pipelines.core.models import (
    PhasedRolloutState,
    PipelineStage,
    PipelineStageAction,
    PipelineStageTrigger,
    ReleasePipeline,
    StageActionType,
    StageTriggerType,
)
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule


@pytest.fixture()
def release_pipeline(project: Project) -> ReleasePipeline:
    release_pipeline = ReleasePipeline.objects.create(
        name="Test Pipeline",
        project=project,
    )
    return release_pipeline  # type: ignore[no-any-return]


@pytest.fixture()
def pipeline_stage_enable_feature_on_enter(
    release_pipeline: ReleasePipeline,
    environment: Environment,
    environment_v2_versioning: Environment,
) -> PipelineStage:
    # Given
    pipeline_stage = PipelineStage.objects.create(
        name="Stage zero",
        pipeline=release_pipeline,
        order=0,
        environment=environment,
    )
    (
        PipelineStageTrigger.objects.create(
            trigger_type=StageTriggerType.ON_ENTER.value, stage=pipeline_stage
        ),
    )
    PipelineStageAction.objects.create(
        action_type=StageActionType.TOGGLE_FEATURE.value,
        action_body={"enabled": True},
        stage=pipeline_stage,
    )
    PipelineStageAction.objects.create(
        action_type=StageActionType.UPDATE_FEATURE_VALUE.value,
        action_body={"string_value": "stage_zero_value", "type": "unicode"},
        stage=pipeline_stage,
    )
    return pipeline_stage


@pytest.fixture()
def rollout_segment(
    project: Project,
) -> Segment:
    segment: Segment = Segment.objects.create(
        name="rollout_segment",
        project=project,
        is_system_segment=True,
    )

    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )

    Condition.objects.create(
        rule=segment_rule, operator=constants.PERCENTAGE_SPLIT, value=20
    )
    return segment


@pytest.fixture()
def phased_rollout_state(
    rollout_segment: Segment,
) -> PhasedRolloutState:
    phased_rollout_state = PhasedRolloutState.objects.create(
        initial_split=20,
        increase_by=20,
        increase_every=timedelta(seconds=60),
        rollout_segment=rollout_segment,
    )
    return phased_rollout_state
