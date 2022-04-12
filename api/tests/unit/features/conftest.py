import pytest

from features.models import FeatureState


@pytest.fixture()
def feature_state_version_generator(environment, feature, request):
    version_1 = request.param[0]
    version_2 = request.param[1]
    expected_result = request.param[2]

    return (
        FeatureState.objects.create(
            feature=feature, environment=environment, version=version_1
        ),
        FeatureState.objects.create(
            feature=feature, environment=environment, version=version_2
        ),
        expected_result,
    )
