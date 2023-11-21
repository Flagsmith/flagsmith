import typing

import pytest

from environments.models import Environment
from features.models import FeatureState

if typing.TYPE_CHECKING:
    from projects.models import Project


@pytest.fixture()
def feature_state_version_generator(environment, feature, request):
    version_1 = request.param[0]
    version_1_live_from = request.param[1]
    version_2 = request.param[2]
    version_2_live_from = request.param[3]
    expected_result = request.param[4]

    return (
        FeatureState.objects.create(
            feature=feature,
            environment=environment,
            version=version_1,
            live_from=version_1_live_from,
        ),
        FeatureState.objects.create(
            feature=feature,
            environment=environment,
            version=version_2,
            live_from=version_2_live_from,
        ),
        expected_result,
    )


@pytest.fixture()
def environment_v2_versioning(project: "Project") -> Environment:
    return Environment.objects.create(
        name="v2_versioning", project=project, use_v2_feature_versioning=True
    )
