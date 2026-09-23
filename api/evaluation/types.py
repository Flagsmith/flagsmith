from typing import TYPE_CHECKING, NamedTuple, TypeAlias

from flag_engine.context import types as context_types
from flag_engine.result import types as result_types

from features.types import FeatureEngineMetadata
from segments.types import SegmentEngineMetadata

if TYPE_CHECKING:
    from features.models import FeatureState


__all__ = (
    "EvaluatedFeatureState",
    "EvaluationContext",
    "EvaluationResult",
    "FeatureContext",
    "FlagResult",
    "IdentityContext",
    "IdentityEvaluation",
    "SegmentContext",
)

EvaluationContext: TypeAlias = context_types.EvaluationContext[
    SegmentEngineMetadata, FeatureEngineMetadata
]
SegmentContext: TypeAlias = context_types.SegmentContext[
    SegmentEngineMetadata, FeatureEngineMetadata
]
FeatureContext: TypeAlias = context_types.FeatureContext[FeatureEngineMetadata]
IdentityContext: TypeAlias = context_types.IdentityContext
EvaluationResult: TypeAlias = result_types.EvaluationResult[
    SegmentEngineMetadata, FeatureEngineMetadata
]
FlagResult: TypeAlias = result_types.FlagResult[FeatureEngineMetadata]


class EvaluatedFeatureState(NamedTuple):
    """A flag as the engine evaluated it, with the feature state it came from.

    Serialise evaluated fields, such as the value and variant, from
    `evaluation_result`, and stored ones, such as ids and configuration, from
    `feature_state`.
    """

    evaluation_result: FlagResult
    feature_state: "FeatureState"


class IdentityEvaluation(NamedTuple):
    result: EvaluationResult
    feature_states: list[EvaluatedFeatureState]
