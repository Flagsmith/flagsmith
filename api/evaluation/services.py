from typing import TYPE_CHECKING

from django.db.models import Q
from flag_engine.engine import get_evaluation_result

from evaluation.mappers import map_environment_to_evaluation_context
from evaluation.types import IdentityEvaluation

if TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from environments.models import Environment


__all__ = ("evaluate_identity",)


def evaluate_identity(
    identity: "Identity",
    *,
    traits: "list[Trait] | None" = None,
    feature_name: str | None = None,
    additional_filters: Q | None = None,
) -> IdentityEvaluation:
    """Evaluate every flag in `identity`'s environment for that identity."""
    environment: "Environment" = identity.environment
    context = map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
        traits=traits,
        segments=environment.get_segments_from_cache(),
        feature_name=feature_name,
        additional_filters=additional_filters,
    )
    result = get_evaluation_result(context)

    # Hand back the rows the engine ruled on, carrying its verdict, so that
    # callers neither re-resolve a value nor work out which row won.
    feature_states = []
    for flag in result["flags"].values():
        feature_state = flag["metadata"]["feature_state"]
        feature_state.flag_result = flag
        feature_states.append(feature_state)

    return IdentityEvaluation(result, feature_states)
