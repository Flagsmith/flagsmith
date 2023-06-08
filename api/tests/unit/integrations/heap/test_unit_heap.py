import pytest

from environments.identities.models import Identity
from environments.models import Environment
from features.models import FeatureState
from integrations.heap.heap import HeapWrapper
from integrations.heap.models import HeapConfiguration


@pytest.mark.django_db
def test_heap_when_generate_user_data_with_correct_values_then_success(
    environment: Environment,
    feature_state: FeatureState,
    feature_state_with_value: FeatureState,
    identity: Identity,
):
    # Given
    api_key = "123key"
    config = HeapConfiguration(api_key=api_key)
    heap_wrapper = HeapWrapper(config)

    # When
    user_data = heap_wrapper.generate_user_data(
        identity=identity, feature_states=[feature_state, feature_state_with_value]
    )

    # Then
    expected_user_data = {
        "app_id": api_key,
        "identity": identity.identifier,
        "event": "Flagsmith Feature Flags",
        "properties": {
            feature_state.feature.name: feature_state.enabled,
            feature_state_with_value.feature.name: feature_state_with_value.get_feature_state_value(
                identity=identity
            ),
        },
    }
    assert expected_user_data == user_data
