import typing

import pytest

from environments.identities.models import Identity
from environments.models import Environment
from features.models import FeatureState
from integrations.amplitude.amplitude import AmplitudeWrapper
from integrations.amplitude.constants import DEFAULT_AMPLITUDE_API_URL
from integrations.amplitude.models import AmplitudeConfiguration


def test_amplitude_initialized_correctly() -> None:
    # Given
    config = AmplitudeConfiguration(api_key="123key")

    # When initialized
    amplitude_wrapper = AmplitudeWrapper(config)

    # Then
    expected_url = f"{DEFAULT_AMPLITUDE_API_URL}/identify"
    assert amplitude_wrapper.url == expected_url


def test_amplitude_initialized_correctly_with_custom_base_url() -> None:
    # Given
    base_url = "https://api.eu.amplitude.com"
    config = AmplitudeConfiguration(api_key="123key", base_url=base_url)

    # When initialized
    amplitude_wrapper = AmplitudeWrapper(config)

    # Then
    assert amplitude_wrapper.url == f"{base_url}/identify"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "initial_value,expected_property_value",
    [(False, False), (True, True), ("foo", "foo"), (1, 1), (0, 0)],
)
def test_amplitude_when_generate_user_data_with_correct_values_then_success(
    initial_value: typing.Any,
    expected_property_value: typing.Any,
    environment: Environment,
    feature_state: FeatureState,
    feature_state_with_value: FeatureState,
    identity: Identity,
) -> None:
    # Given
    api_key = "123key"

    config = AmplitudeConfiguration(api_key=api_key)
    amplitude_wrapper = AmplitudeWrapper(config)

    # When
    user_data = amplitude_wrapper.generate_user_data(
        identity=identity,
        feature_states=[feature_state, feature_state_with_value],
        trait_models=[],
    )

    # Then
    feature_properties = {
        feature_state.feature.name: feature_state.enabled,
        feature_state_with_value.feature.name: expected_property_value,
    }

    expected_user_data = {
        "user_id": identity.identifier,
        "user_properties": feature_properties,
    }

    assert expected_user_data == user_data
