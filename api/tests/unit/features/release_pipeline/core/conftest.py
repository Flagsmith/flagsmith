import pytest
import pytest
from django.utils import timezone
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
from segments.models import Segment
from users.models import FFAdminUser


@pytest.fixture()
def release_pipeline(project: Project) -> ReleasePipeline:
    return ReleasePipeline.objects.create(
        name="Test Pipeline",
        project=project,
    )
