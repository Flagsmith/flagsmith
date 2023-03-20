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


@pytest.fixture()
def feature_state_live_from_generator(environment, feature, request):
    live_from_one = request.param[0]
    live_from_two = request.param[1]
    expected_result = request.param[2]

    return (
        FeatureState.objects.create(
            feature=feature, environment=environment, live_from=live_from_one, version=2
        ),
        FeatureState.objects.create(
            feature=feature, environment=environment, live_from=live_from_two, version=3
        ),
        expected_result,
    )
