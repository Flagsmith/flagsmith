"""Helpers for asserting how flag-engine evaluates a feature state.

Multivariate allocation moved into the engine, so tests that used to probe it
via `FeatureState.get_multivariate_feature_state_value(key)` ask the engine the
same question here, for a bare identity key rather than a persisted identity.
"""

from typing import TYPE_CHECKING, Any, NamedTuple

from features.evaluation import evaluate_feature_state as _evaluate_feature_state

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
    flag_result = _evaluate_feature_state(feature_state, str(identity_key))
    return EvaluatedFlag(flag_result["value"], flag_result["variant"])
