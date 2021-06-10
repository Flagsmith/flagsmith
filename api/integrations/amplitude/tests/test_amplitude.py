import pytest

from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.amplitude.amplitude import (
    AMPLITUDE_API_URL,
    AmplitudeWrapper,
)
from organisations.models import Organisation
from projects.models import Project


def test_amplitude_initialized_correctly():
    # Given
    api_key = "123key"

    # When initialized
    amplitude_wrapper = AmplitudeWrapper(api_key=api_key)

    # Then
    expected_url = f"{AMPLITUDE_API_URL}/identify"
    assert amplitude_wrapper.url == expected_url


@pytest.mark.django_db
def test_amplitude_when_generate_user_data_with_correct_values_then_success():
    # Given
    api_key = "123key"
    user_id = "user123"
    amplitude_wrapper = AmplitudeWrapper(api_key=api_key)

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    environment_one = Environment.objects.create(
        name="Test Environment 1", project=project
    )
    feature = Feature.objects.create(name="Test Feature", project=project)
    feature_states = FeatureState.objects.filter(feature=feature)

    # When
    user_data = amplitude_wrapper.generate_user_data(
        user_id=user_id, feature_states=feature_states
    )

    # Then

    feature_properties = {}

    for feature_state in feature_states:
        value = feature_state.get_feature_state_value()
        feature_properties[feature_state.feature.name] = (
            value if (feature_state.enabled and value) else feature_state.enabled
        )

    expected_user_data = {
        "user_id": user_id,
        "user_properties": feature_properties,
    }

    assert expected_user_data == user_data
