import pytest

from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.amplitude.amplitude import AmplitudeWrapper, AMPLITUDE_API_URL
from organisations.models import Organisation
from projects.models import Project


def test_amplitude_initialized_correctly():
    # Given
    api_key = '123key'

    # When initialized
    amplitude_wrapper = AmplitudeWrapper(api_key=api_key)

    # Then
    expected_url = f"{AMPLITUDE_API_URL}/identify?api_key={api_key}"
    assert amplitude_wrapper.url == expected_url


@pytest.mark.django_db
def test_amplitude_when_generate_user_data_with_correct_values_then_success():
    # Given
    api_key = '123key'
    user_id = 'user123'
    amplitude_wrapper = AmplitudeWrapper(api_key=api_key)

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    environment_one = Environment.objects.create(name="Test Environment 1", project=project)
    feature = Feature.objects.create(name="Test Feature", project=project)
    feature_states = FeatureState.objects.filter(feature=feature)

    # When
    user_data = amplitude_wrapper.generate_user_data(user_id=user_id,
                                                     feature_states=feature_states)

    # Then
    expected_user_data = {
        "identification": {
            "user_id": user_id,
            "user_properties": {
                feature_state.feature.name: feature_state.get_feature_state_value()
                if feature_state.get_feature_state_value() is not None else "None"
                for feature_state in feature_states
            }
        }
    }
    assert expected_user_data == user_data
