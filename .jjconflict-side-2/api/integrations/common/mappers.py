from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from evaluation.types import EvaluatedFeatureState


def map_feature_states_to_feature_properties(
    feature_states: "Iterable[EvaluatedFeatureState]",
) -> dict[str, Any]:
    """Each flag's value, or whether it's enabled if it's disabled or has no value."""
    flags = [feature_state.evaluation_result for feature_state in feature_states]
    return {
        flag["name"]: (
            flag["value"]
            if flag["enabled"] and flag["value"] is not None
            else flag["enabled"]
        )
        for flag in flags
    }
