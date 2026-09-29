from typing import TYPE_CHECKING

from django.db.models import Q
from flag_engine.engine import get_evaluation_result

from evaluation.mappers import map_environment_to_evaluation_context
from evaluation.types import (
    EvaluatedFeatureState,
    EvaluationResult,
    IdentityEvaluation,
)

if TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from environments.models import Environment


__all__ = (
    "evaluate_identity",
    "get_environment_feature_states",
    "get_identity_feature_states",
)


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
    return IdentityEvaluation(result, _map_result_to_evaluated_feature_states(result))


def get_identity_feature_states(
    identity: "Identity",
    *,
    traits: "list[Trait] | None" = None,
    additional_filters: Q | None = None,
) -> list[EvaluatedFeatureState]:
    """The flags to serve `identity`, one per feature."""
    _, evaluated_feature_states = evaluate_identity(
        identity,
        traits=traits,
        additional_filters=additional_filters,
    )
    return _hide_disabled_flags(identity.environment, evaluated_feature_states)


def get_environment_feature_states(
    environment: "Environment",
    *,
    additional_filters: Q | None = None,
    from_replica: bool = False,
) -> list[EvaluatedFeatureState]:
    """The flags to serve for an environment, one per feature."""
    context = map_environment_to_evaluation_context(
        environment=environment,
        additional_filters=additional_filters,
        from_replica=from_replica,
    )
    result = get_evaluation_result(context)
    return _hide_disabled_flags(
        environment, _map_result_to_evaluated_feature_states(result)
    )


def _map_result_to_evaluated_feature_states(
    result: EvaluationResult,
) -> list[EvaluatedFeatureState]:
    return [
        EvaluatedFeatureState(
            evaluation_result=flag,
            feature_state=flag["metadata"]["feature_state"],
        )
        for flag in result["flags"].values()
    ]


def _hide_disabled_flags(
    environment: "Environment",
    evaluated_feature_states: list[EvaluatedFeatureState],
) -> list[EvaluatedFeatureState]:
    if environment.get_hide_disabled_flags() is True:
        return [
            evaluated_feature_state
            for evaluated_feature_state in evaluated_feature_states
            if evaluated_feature_state.evaluation_result["enabled"]
        ]
    return evaluated_feature_states
