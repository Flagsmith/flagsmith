from math import inf
from typing import TYPE_CHECKING

from django.db.models import Q
from flag_engine.engine import get_evaluation_result

from evaluation.mappers import (
    IDENTITY_OVERRIDES_SEGMENT_KEY,
    map_edge_identity_to_identity_context,
    map_engine_feature_state_to_feature_context,
    map_environment_to_evaluation_context,
    map_identity_overrides_to_segment_context,
)
from evaluation.types import IdentityEvaluation

if TYPE_CHECKING:
    from edge_api.identities.models import EdgeIdentity
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from environments.models import Environment
    from features.models import FeatureState
    from segments.models import Segment
    from util.engine_models.features.models import FeatureStateModel


__all__ = (
    "evaluate_identity",
    "get_environment_feature_states",
    "get_edge_identity_feature_states",
    "get_edge_identity_segments",
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


def get_edge_identity_feature_states(
    edge_identity: "EdgeIdentity",
) -> "list[FeatureState | FeatureStateModel]":
    """The feature states to serve an edge identity, one per feature.

    An edge identity's own overrides live in DynamoDB rather than the ORM, so
    they are laid over the evaluated environment afterwards, and are the only
    states in the returned list not carrying a `flag_result`.
    """
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
        context.setdefault("segments", {})[IDENTITY_OVERRIDES_SEGMENT_KEY] = (
            map_identity_overrides_to_segment_context(overrides)
        )

    feature_states: list["FeatureState | FeatureStateModel"] = []
    for flag in get_evaluation_result(context)["flags"].values():
        if (feature_state := flag["metadata"].get("feature_state")) is not None:
            feature_state.flag_result = flag
            feature_states.append(feature_state)
        else:
            # A stored model cannot be assigned the engine's verdict, so an
            # edge identity's own overrides are still resolved by the
            # serialiser. See Flagsmith/flagsmith-engine#340.
            feature_states.append(flag["metadata"]["edge_feature_state"])

    return feature_states


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


def get_environment_feature_states(
    environment: "Environment",
    *,
    additional_filters: Q | None = None,
    from_replica: bool = False,
) -> "list[FeatureState]":
    """The feature states to serve for an environment, one per feature.

    Evaluated without an identity, so a segment whose rules read a trait or
    split on the identity key cannot match. One reading `$.environment`, or
    another flag, still can — as it does for an SDK evaluating locally.
    """
    context = map_environment_to_evaluation_context(
        environment=environment,
        segments=environment.get_segments_from_cache(),
        additional_filters=additional_filters,
        from_replica=from_replica,
    )
    result = get_evaluation_result(context)

    hide_disabled_flags = environment.get_hide_disabled_flags() is True
    feature_states = []
    for flag in result["flags"].values():
        if hide_disabled_flags and not flag["enabled"]:
            continue
        feature_state = flag["metadata"]["feature_state"]
        feature_state.flag_result = flag
        feature_states.append(feature_state)

    return feature_states
