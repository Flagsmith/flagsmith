import pytest

from environments.identities.models import Identity
from environments.models import Environment
from features.models import FeatureState
from integrations.amplitude.amplitude import (
    AMPLITUDE_API_URL,
    AmplitudeWrapper,
)
from integrations.amplitude.models import AmplitudeConfiguration


def test_amplitude_initialized_correctly():
    # Given
    config = AmplitudeConfiguration(api_key="123key")

    # When initialized
    amplitude_wrapper = AmplitudeWrapper(config)

    # Then
    expected_url = f"{AMPLITUDE_API_URL}/identify"
    assert amplitude_wrapper.url == expected_url


@pytest.mark.django_db
def test_amplitude_when_generate_user_data_with_correct_values_then_success(
    environment: Environment,
    feature_state: FeatureState,
    feature_state_with_value: FeatureState,
    identity: Identity,
):
    # Given
    api_key = "123key"

    config = AmplitudeConfiguration(api_key=api_key)
    amplitude_wrapper = AmplitudeWrapper(config)

    # When
    user_data = amplitude_wrapper.generate_user_data(
        identity=identity, feature_states=[feature_state, feature_state_with_value]
    )

    # Then
    feature_properties = {
        feature_state.feature.name: feature_state.enabled,
        feature_state_with_value.feature.name: feature_state_with_value.get_feature_state_value(
            identity=identity
        ),
    }

    expected_user_data = {
        "user_id": identity.identifier,
        "user_properties": feature_properties,
    }

    assert expected_user_data == user_data
