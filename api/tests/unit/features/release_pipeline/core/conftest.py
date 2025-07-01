import pytest

from features.release_pipelines.core.models import (
    ReleasePipeline,
)
from projects.models import Project


@pytest.fixture()
def release_pipeline(project: Project) -> ReleasePipeline:
    return ReleasePipeline.objects.create(
        name="Test Pipeline",
        project=project,
    )
