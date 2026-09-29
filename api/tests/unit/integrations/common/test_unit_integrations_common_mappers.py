import typing

import pytest

from evaluation.types import EvaluatedFeatureState
from features.models import FeatureState
from integrations.common.mappers import map_feature_states_to_feature_properties


@pytest.mark.parametrize(
    "enabled, value, expected_property",
    [
        pytest.param(True, "value", "value", id="enabled_with_value"),
        pytest.param(True, 0, 0, id="enabled_with_zero"),
        pytest.param(True, False, False, id="enabled_with_false"),
        pytest.param(True, "", "", id="enabled_with_empty_string"),
        pytest.param(True, None, True, id="enabled_without_value"),
        pytest.param(False, "value", False, id="disabled_with_value"),
        pytest.param(False, None, False, id="disabled_without_value"),
    ],
)
def test_map_feature_states_to_feature_properties__flag__returns_expected_property(
    feature_state: FeatureState,
    enabled: bool,
    value: typing.Any,
    expected_property: typing.Any,
) -> None:
    # Given
    evaluated_feature_state = EvaluatedFeatureState(
        evaluation_result={
            "name": "feature",
            "enabled": enabled,
            "value": value,
            "reason": "DEFAULT",
            "variant": None,
            "metadata": {"feature_state": feature_state},
        },
        feature_state=feature_state,
    )

    # When
    feature_properties = map_feature_states_to_feature_properties(
        [evaluated_feature_state]
    )

    # Then
    assert feature_properties == {"feature": expected_property}
