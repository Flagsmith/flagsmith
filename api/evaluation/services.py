from typing import TYPE_CHECKING

from django.db.models import Q
from flag_engine.engine import get_evaluation_result

from evaluation.mappers import map_environment_to_evaluation_context
from evaluation.types import IdentityEvaluation

if TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from environments.models import Environment
    from features.models import FeatureState


__all__ = ("evaluate_identity", "get_identity_feature_states")


def evaluate_identity(
    identity: "Identity",
    *,
    traits: "list[Trait] | None" = None,
    additional_filters: Q | None = None,
) -> IdentityEvaluation:
    """Evaluate every flag in `identity`'s environment for that identity."""
    environment: "Environment" = identity.environment
    context = map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
        traits=traits,
        segments=environment.get_segments_from_cache(),
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


def get_identity_feature_states(
    identity: "Identity",
    *,
    traits: "list[Trait] | None" = None,
    additional_filters: Q | None = None,
) -> "list[FeatureState]":
    """The feature states to serve `identity`, one per feature.

    Each carries the engine's verdict on `flag_result`, so a caller reads the
    evaluated value and variant off the row rather than resolving them again.
    """
    _, feature_states = evaluate_identity(
        identity,
        traits=traits,
        additional_filters=additional_filters,
    )

    if identity.environment.get_hide_disabled_flags() is True:
        return [
            feature_state for feature_state in feature_states if feature_state.enabled
        ]

    return feature_states
