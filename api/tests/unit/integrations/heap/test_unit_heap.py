import typing

import pytest

from environments.identities.models import Identity
from environments.models import Environment
from features.models import FeatureState
from integrations.heap.heap import HeapWrapper
from integrations.heap.models import HeapConfiguration


@pytest.mark.django_db
@pytest.mark.parametrize(
    "feature_state_with_value,expected_property_value",
    [(False, False), (True, True), ("foo", "foo"), (1, 1), (0, 0)],
    indirect=["feature_state_with_value"],
)
def test_heap_when_generate_user_data_with_correct_values_then_success(
    expected_property_value: typing.Any,
    environment: Environment,
    feature_state: FeatureState,
    feature_state_with_value: FeatureState,
    identity: Identity,
) -> None:
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
            feature_state_with_value.feature.name: expected_property_value,
        },
    }
    assert expected_user_data == user_data
