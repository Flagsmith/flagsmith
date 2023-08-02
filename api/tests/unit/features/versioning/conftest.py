import typing

import pytest

from environments.models import Environment

if typing.TYPE_CHECKING:
    from projects.models import Project


@pytest.fixture()
def environment_v2_versioning(project: "Project") -> Environment:
    return Environment.objects.create(
        name="v2_versioning", project=project, use_v2_feature_versioning=True
    )
