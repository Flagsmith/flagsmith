from collections.abc import Iterable
from math import inf
from typing import TYPE_CHECKING, Any

from flag_engine.context import types as engine_types
from flag_engine.engine import get_evaluation_result

from evaluation.mappers import (
    IDENTITY_OVERRIDES_SEGMENT_NAME,
    map_edge_identity_to_identity_context,
    map_engine_feature_state_to_feature_context,
    map_environment_to_evaluation_context,
    map_identity_overrides_to_segment_context,
)
from evaluation.types import (
    EvaluatedFeatureState,
    EvaluationResult,
    IdentityEvaluation,
)

if TYPE_CHECKING:
    from edge_api.identities.models import EdgeIdentity
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from environments.models import Environment
    from features.models import FeatureState
    from segments.models import Segment
    from util.engine_models.features.models import FeatureStateModel


_IDENTITY_FREE_PROPERTY_PREFIXES = ("$.environment.", "$.flags.")

__all__ = (
    "evaluate_identity",
    "get_edge_identity_feature_states",
    "get_edge_identity_override_value",
    "get_edge_identity_segments",
    "get_environment_feature_states",
    "get_identity_feature_states",
)


def evaluate_identity(
    identity: "Identity",
    *,
    traits: "list[Trait] | None" = None,
) -> IdentityEvaluation:
    """Evaluate every flag in `identity`'s environment for that identity."""
    environment: "Environment" = identity.environment
    context = map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
        traits=traits,
        segments=environment.get_segments_from_cache(),
    )
    result = get_evaluation_result(context)
    return IdentityEvaluation(result, _map_result_to_evaluated_feature_states(result))


def get_identity_feature_states(
    identity: "Identity",
    *,
    traits: "list[Trait] | None" = None,
    hide_server_key_only: bool = False,
) -> list[EvaluatedFeatureState]:
    """The flags to serve `identity`, one per feature."""
    _, evaluated_feature_states = evaluate_identity(identity, traits=traits)
    return _hide_flags(
        identity.environment,
        evaluated_feature_states,
        hide_server_key_only=hide_server_key_only,
    )


def get_environment_feature_states(
    environment: "Environment",
    *,
    hide_server_key_only: bool = False,
    from_replica: bool = False,
) -> list[EvaluatedFeatureState]:
    """The flags to serve for an environment, one per feature.

    Evaluated without an identity, so segments reading traits or identity
    context are left out.
    """
    context = map_environment_to_evaluation_context(
        environment=environment,
        segments=environment.get_segments_from_cache(),
        from_replica=from_replica,
    )
    if segments := context.get("segments"):
        context["segments"] = {
            key: segment
            for key, segment in segments.items()
            if _is_identity_free(segment["rules"])
        }
    result = get_evaluation_result(context)
    return _hide_flags(
        environment,
        _map_result_to_evaluated_feature_states(result),
        hide_server_key_only=hide_server_key_only,
    )


def get_edge_identity_feature_states(
    edge_identity: "EdgeIdentity",
) -> "list[EvaluatedFeatureState[FeatureState | FeatureStateModel]]":
    """The flags to serve an edge identity, one per feature."""
    environment: "Environment" = edge_identity.environment

    context = map_environment_to_evaluation_context(
        environment=environment,
        identity_context=map_edge_identity_to_identity_context(
            edge_identity, environment=environment
        ),
        segments=environment.get_segments_from_cache(),
    )
    # The identity's own overrides are read back from DynamoDB rather than the
    # ORM, so the mapper never saw them. They reach the engine the way every
    # identity override does, as a segment no other override can outrank.
    if overrides := [
        map_engine_feature_state_to_feature_context(feature_state, priority=-inf)
        for feature_state in edge_identity.feature_overrides
    ]:
        context.setdefault("segments", {})[IDENTITY_OVERRIDES_SEGMENT_NAME] = (
            map_identity_overrides_to_segment_context(overrides)
        )

    return [
        EvaluatedFeatureState(
            evaluation_result=flag,
            feature_state=(
                feature_state
                if (feature_state := flag["metadata"].get("feature_state")) is not None
                else flag["metadata"]["edge_feature_state"]
            ),
        )
        for flag in get_evaluation_result(context)["flags"].values()
    ]


def get_edge_identity_override_value(
    edge_identity: "EdgeIdentity",
    feature_state: "FeatureStateModel",
    *,
    environment: "Environment",
) -> Any:
    """The value `edge_identity` is served by its own override `feature_state`."""
    # TODO: Read the stored value instead, once identity overrides can only hold
    # a single variant, as per https://github.com/Flagsmith/flagsmith/issues/8597
    feature_context = map_engine_feature_state_to_feature_context(feature_state)
    flag_name = feature_context["name"]
    result = get_evaluation_result(
        {
            "environment": {
                "key": environment.api_key,
                "name": environment.name or "",
            },
            "identity": map_edge_identity_to_identity_context(
                edge_identity, environment=environment
            ),
            "features": {flag_name: feature_context},
        }
    )
    return result["flags"][flag_name]["value"]


def get_edge_identity_segments(edge_identity: "EdgeIdentity") -> "list[Segment]":
    """The segments an edge identity belongs to."""
    environment: "Environment" = edge_identity.environment
    segments: "list[Segment]" = environment.project.get_segments_from_cache()
    segments_by_pk = {segment.pk: segment for segment in segments}

    context = map_environment_to_evaluation_context(
        environment=environment,
        identity_context=map_edge_identity_to_identity_context(
            edge_identity, environment=environment
        ),
        segments=segments,
    )

    return [
        segments_by_pk[pk]
        for segment_result in get_evaluation_result(context)["segments"]
        if (pk := segment_result["metadata"].get("pk")) is not None
    ]


def _is_identity_free(rules: "Iterable[engine_types.SegmentRule]") -> bool:
    return all(
        all(
            condition["property"].startswith(_IDENTITY_FREE_PROPERTY_PREFIXES)
            for condition in rule.get("conditions", [])
        )
        and _is_identity_free(rule.get("rules", []))
        for rule in rules
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


def _hide_flags(
    environment: "Environment",
    evaluated_feature_states: list[EvaluatedFeatureState],
    *,
    hide_server_key_only: bool,
) -> list[EvaluatedFeatureState]:
    hide_disabled = environment.get_hide_disabled_flags() is True
    return [
        evaluated_feature_state
        for evaluated_feature_state in evaluated_feature_states
        if not (
            hide_disabled and not evaluated_feature_state.evaluation_result["enabled"]
        )
        and not (
            hide_server_key_only
            and evaluated_feature_state.feature_state.feature.is_server_key_only
        )
    ]
