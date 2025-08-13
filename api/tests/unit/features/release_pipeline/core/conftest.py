from datetime import timedelta

import pytest
from django.utils import timezone
from flag_engine.segments import constants

from environments.models import Environment
from features.models import Feature
from features.release_pipelines.core.models import (
    PhasedRolloutState,
    PipelineStage,
    PipelineStageAction,
    PipelineStageTrigger,
    ReleasePipeline,
    StageActionType,
    StageTriggerType,
)
from features.versioning.models import EnvironmentFeatureVersion
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from users.models import FFAdminUser


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
    return create_rollout_segment(project)


def create_rollout_segment(
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
def pipeline_stage_update_feature_value_on_wait_for(
    release_pipeline: ReleasePipeline,
    environment: Environment,
    identity_matching_segment: Segment,
) -> PipelineStage:
    # Given
    pipeline_stage = PipelineStage.objects.create(
        name="Stage one",
        pipeline=release_pipeline,
        order=1,
        environment=environment,
    )
    PipelineStageTrigger.objects.create(
        trigger_type=StageTriggerType.WAIT_FOR.value,
        stage=pipeline_stage,
        trigger_body={"wait_for": "00:00:01"},
    )
    PipelineStageAction.objects.create(
        action_type=StageActionType.TOGGLE_FEATURE.value,
        action_body={"enabled": False},
        stage=pipeline_stage,
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
            "segment_id": identity_matching_segment.id,
        },
        stage=pipeline_stage,
    )
    PipelineStageAction.objects.create(
        action_type=StageActionType.TOGGLE_FEATURE_FOR_SEGMENT.value,
        action_body={"enabled": False, "segment_id": identity_matching_segment.id},
        stage=pipeline_stage,
    )
    return pipeline_stage


@pytest.fixture()
def pipeline_stage_phased_rollout(
    release_pipeline: ReleasePipeline,
    environment: Environment,
) -> PipelineStage:
    pipeline_stage = PipelineStage.objects.create(
        name="Stage phased rollout",
        pipeline=release_pipeline,
        order=3,
        environment=environment,
    )
    PipelineStageTrigger.objects.create(
        trigger_type=StageTriggerType.ON_ENTER.value,
        stage=pipeline_stage,
    )
    PipelineStageAction.objects.create(
        action_type=StageActionType.PHASED_ROLLOUT.value,
        action_body={
            "initial_split": 20,
            "increase_by": 20,
            "increase_every": "00:01:00",
            "enabled": True,
            "string_value": "phased_rollout_value",
            "type": "unicode",
        },
        stage=pipeline_stage,
    )
    return pipeline_stage


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


@pytest.fixture()
def complete_phased_rollout_state(project: Project) -> PhasedRolloutState:
    rollout_segment = create_rollout_segment(project)
    phased_rollout_state = PhasedRolloutState.objects.create(
        rollout_segment=rollout_segment,
        initial_split=20,
        increase_by=20,
        is_rollout_complete=True,
        increase_every=timedelta(seconds=60),
    )
    return phased_rollout_state


@pytest.fixture()
def feature_in_pipeline_stage_enable_feature_on_enter(
    pipeline_stage_enable_feature_on_enter: PipelineStage,
    admin_user: FFAdminUser,
) -> Feature:
    feature: Feature = Feature.objects.create(
        name="feature_in_pipeline_stage_enable_feature_on_enter",
        project=pipeline_stage_enable_feature_on_enter.pipeline.project,
    )
    EnvironmentFeatureVersion.objects.create(
        feature_id=feature.id,
        environment=pipeline_stage_enable_feature_on_enter.environment,
        published_by=admin_user,
        pipeline_stage=pipeline_stage_enable_feature_on_enter,
    )
    return feature


@pytest.fixture()
def feature_in_pipeline_stage_update_feature_value_on_wait_for(
    pipeline_stage_update_feature_value_on_wait_for: PipelineStage,
    admin_user: FFAdminUser,
) -> Feature:
    feature: Feature = Feature.objects.create(
        name="feature_in_pipeline_stage_update_feature_value_on_wait_for",
        project=pipeline_stage_update_feature_value_on_wait_for.pipeline.project,
    )
    EnvironmentFeatureVersion.objects.create(
        feature_id=feature.id,
        environment=pipeline_stage_update_feature_value_on_wait_for.environment,
        published_by=admin_user,
        pipeline_stage=pipeline_stage_update_feature_value_on_wait_for,
    )
    return feature


@pytest.fixture()
def feature_in_pipeline_stage_phased_rollout(
    pipeline_stage_phased_rollout: PipelineStage,
    phased_rollout_state: PhasedRolloutState,
    admin_user: FFAdminUser,
) -> Feature:
    feature: Feature = Feature.objects.create(
        name="feature_in_pipeline_stage_phased_rollout",
        project=pipeline_stage_phased_rollout.pipeline.project,
    )
    EnvironmentFeatureVersion.objects.create(
        feature_id=feature.id,
        environment=pipeline_stage_phased_rollout.environment,
        published_by=admin_user,
        pipeline_stage=pipeline_stage_phased_rollout,
        published_at=timezone.now(),
        phased_rollout_state=phased_rollout_state,
    )
    return feature


@pytest.fixture()
def feature_completed_pipeline_phased_rollout(
    pipeline_stage_phased_rollout: PipelineStage,
    complete_phased_rollout_state: PhasedRolloutState,
    admin_user: FFAdminUser,
) -> Feature:
    feature: Feature = Feature.objects.create(
        name="feature_completed_pipeline_phased_rollout",
        project=pipeline_stage_phased_rollout.pipeline.project,
    )
    EnvironmentFeatureVersion.objects.create(
        feature_id=feature.id,
        environment=pipeline_stage_phased_rollout.environment,
        published_by=admin_user,
        published_at=timezone.now(),
        pipeline_stage=pipeline_stage_phased_rollout,
        phased_rollout_state=complete_phased_rollout_state,
    )
    return feature
