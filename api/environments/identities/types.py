from typing import TYPE_CHECKING, NamedTuple

from evaluation.types import EvaluationContext, EvaluationResult

if TYPE_CHECKING:
    from features.models import FeatureState


__all__ = (
    "IdentityEvaluation",
    "IdentityEvaluationContext",
)


class IdentityEvaluationContext(NamedTuple):
    context: EvaluationContext
    feature_states_by_id: "dict[int, FeatureState]"


class IdentityEvaluation(NamedTuple):
    result: EvaluationResult
    feature_states_by_id: "dict[int, FeatureState]"
