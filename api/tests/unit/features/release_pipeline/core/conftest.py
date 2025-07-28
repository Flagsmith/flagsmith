import pytest

from environments.models import Environment
from features.release_pipelines.core.models import (
    PipelineStage,
    PipelineStageAction,
    PipelineStageTrigger,
    ReleasePipeline,
    StageActionType,
    StageTriggerType,
)
from projects.models import Project


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
