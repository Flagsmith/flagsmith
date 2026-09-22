from typing import TYPE_CHECKING, NamedTuple, TypeAlias

from flag_engine.context import types as context_types
from flag_engine.result import types as result_types

from features.types import FeatureEngineMetadata
from segments.types import SegmentEngineMetadata

if TYPE_CHECKING:
    from features.models import FeatureState


__all__ = (
    "EvaluationContext",
    "EvaluationResult",
    "FeatureContext",
    "FlagResult",
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
EvaluationResult: TypeAlias = result_types.EvaluationResult[
    SegmentEngineMetadata, FeatureEngineMetadata
]
FlagResult: TypeAlias = result_types.FlagResult[FeatureEngineMetadata]


class IdentityEvaluation(NamedTuple):
    result: EvaluationResult
    #: The feature states evaluated, by id. `FlagResult.metadata` carries a
    #: `feature_state_id`, so a caller still working in Django rows can reach
    #: the one a flag came from.
    feature_states_by_id: "dict[int, FeatureState]"
