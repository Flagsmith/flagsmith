"""Helpers for asserting how flag-engine evaluates a feature state.

Multivariate allocation moved into the engine, so tests that used to probe it
via `FeatureState.get_multivariate_feature_state_value(key)` ask the engine the
same question here, for a bare identity key rather than a persisted identity.
"""

from typing import TYPE_CHECKING, Any, NamedTuple

from flag_engine.engine import get_evaluation_result

from util.mappers.engine import EvaluationContext, map_feature_state_to_feature_context

if TYPE_CHECKING:
    from features.models import FeatureState


__all__ = ("EvaluatedFlag", "evaluate_feature_state")


class EvaluatedFlag(NamedTuple):
    value: Any
    variant: str | None


def evaluate_feature_state(
    feature_state: "FeatureState",
    identity_key: str | int,
) -> EvaluatedFlag:
    """Evaluate `feature_state` as the engine would, for `identity_key`."""
    feature_name = feature_state.feature.name
    context: EvaluationContext = {
        "environment": {"key": "", "name": ""},
        "identity": {"identifier": "", "key": str(identity_key)},
        "features": {
            feature_name: map_feature_state_to_feature_context(
                feature_state,
                mv_fs_values=feature_state.multivariate_feature_state_values.all(),
            )
        },
    }
    flag_result = get_evaluation_result(context)["flags"][feature_name]
    return EvaluatedFlag(flag_result["value"], flag_result["variant"])
