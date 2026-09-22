"""Mapping Django ORM models to a flag-engine `EvaluationContext`.

Core API's whole contribution to flag evaluation: resolve the rows that are
current for an environment, lay them out as the engine expects, and let it
decide which override wins and which variant an identity lands in.
"""

from collections.abc import Iterable
from math import inf
from operator import attrgetter
from typing import TYPE_CHECKING, NamedTuple

from django.db.models import Prefetch, Q
from flag_engine.context import types as engine_types
from flag_engine.segments.constants import IS_SET
from flag_engine.segments.types import ConditionOperator, RuleType
from pydantic import TypeAdapter

from evaluation.types import EvaluationContext, FeatureContext, SegmentContext
from features.types import FeatureEngineMetadata
from segments.types import SegmentEngineMetadata

if TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from environments.models import Environment
    from features.models import FeatureState
    from features.multivariate.models import MultivariateFeatureStateValue
    from segments.models import Condition, Segment, SegmentRule


__all__ = (
    "IDENTITY_OVERRIDES_SEGMENT_KEY",
    "IDENTITY_OVERRIDES_SEGMENT_NAME",
    "map_condition_to_segment_condition",
    "map_environment_to_evaluation_context",
    "map_feature_state_to_feature_context",
    "map_rule_to_segment_rule",
    "map_segment_to_segment_context",
)


IDENTITY_OVERRIDES_SEGMENT_KEY = IDENTITY_OVERRIDES_SEGMENT_NAME = "identity_overrides"


_rule_type_adapter: TypeAdapter[RuleType] = TypeAdapter(RuleType)
_condition_operator_adapter: TypeAdapter[ConditionOperator] = TypeAdapter(
    ConditionOperator
)


def map_environment_to_evaluation_context(
    *,
    environment: "Environment",
    identity: "Identity | None" = None,
    traits: "Iterable[Trait] | None" = None,
    segments: "Iterable[Segment] | None" = None,
    additional_filters: "Q | None" = None,
) -> EvaluationContext:
    """Map Django ORM models to a flag-engine `EvaluationContext`.

    Resolves the feature states that are current for `environment` — defaults,
    segment overrides, and `identity`'s own overrides — and lays them out as
    `$.features` plus the overrides carried on each segment.

    Each feature context carries the row it was built from as metadata, which
    the engine hands back on the corresponding `FlagResult`, so a caller still
    working in Django rows never has to work out which override won.

    :param segments: segments to evaluate.
    """
    context: EvaluationContext = {
        "environment": {
            "key": environment.api_key,
            "name": environment.name or "",
        },
    }
    if identity is not None:
        trait_items: "Iterable[Trait]" = (
            traits
            if traits is not None
            # A transient identity was never persisted, so it has no stored
            # traits to read, and asking for them would raise.
            else identity.identity_traits.all()
            if identity.pk
            else ()
        )
        identity_traits = {trait.trait_key: trait.trait_value for trait in trait_items}
        if identity.system_traits:
            # System-owned traits are not user data: on a key clash, the system
            # value wins.
            identity_traits.update(identity.system_traits)
        context["identity"] = {
            "identifier": identity.identifier,
            "key": identity.get_hash_key(
                environment.use_identity_composite_key_for_hashing
            ),
            "traits": identity_traits,
        }

    (
        feature_states,
        identity_overrides,
        segment_overrides,
        mv_fs_values_by_feature_state_id,
    ) = _resolve_feature_states(
        environment=environment,
        identity=identity,
        additional_filters=additional_filters,
    )

    # No reading from ORM past this point!

    def to_feature_context(
        feature_state: "FeatureState",
        *,
        priority: float | None = None,
    ) -> FeatureContext:
        return map_feature_state_to_feature_context(
            feature_state,
            mv_fs_values=mv_fs_values_by_feature_state_id.get(feature_state.pk),
            priority=priority,
        )

    if segments is not None:
        context["segments"] = {
            str(segment.pk): map_segment_to_segment_context(
                segment,
                overrides=[
                    to_feature_context(feature_state)
                    for feature_state in segment_overrides.get(segment.pk) or ()
                ],
            )
            for segment in segments
        }

    if identity_overrides:
        # An identity override outranks every segment override, which the
        # engine expresses as a priority no segment can beat.
        context.setdefault("segments", {})[IDENTITY_OVERRIDES_SEGMENT_KEY] = (
            _map_identity_overrides_to_segment_context(
                [
                    to_feature_context(feature_state, priority=-inf)
                    for feature_state in identity_overrides
                ]
            )
        )

    context["features"] = {
        (feature_context := to_feature_context(feature_state))["name"]: feature_context
        for feature_state in feature_states
    }

    return context


class _ResolvedFeatureStates(NamedTuple):
    feature_states: list["FeatureState"]
    identity_overrides: list["FeatureState"]
    segment_overrides: dict[int, list["FeatureState"]]
    mv_fs_values_by_feature_state_id: dict[
        int, "Iterable[MultivariateFeatureStateValue]"
    ]


def _resolve_feature_states(
    *,
    environment: "Environment",
    identity: "Identity | None",
    additional_filters: "Q | None",
) -> _ResolvedFeatureStates:
    """Read the feature states current for `environment`, split by what they override."""
    # Deferred: `environments.models` imports this module's package.
    from features.multivariate.models import MultivariateFeatureStateValue
    from features.versioning.versioning_service import get_environment_flags_list

    override_filters = Q(identity__isnull=True)
    if identity is not None and identity.pk:
        # The identity is persisted (non-transient).
        # Look for its identity overrides in addition to segment overrides.
        override_filters = Q(identity=identity) | override_filters
    if additional_filters:
        override_filters &= additional_filters

    feature_states = get_environment_flags_list(
        environment=environment,
        additional_filters=override_filters,
        additional_select_related_args=["feature_segment__segment"],
        additional_prefetch_related_args=[
            Prefetch(
                "multivariate_feature_state_values",
                queryset=MultivariateFeatureStateValue.objects.select_related(
                    "multivariate_feature_option"
                ),
            )
        ],
    )

    resolved = _ResolvedFeatureStates([], [], {}, {})

    for feature_state in feature_states:
        resolved.mv_fs_values_by_feature_state_id[feature_state.pk] = (
            feature_state.multivariate_feature_state_values.all()
        )
        if feature_state.identity_id is not None:
            resolved.identity_overrides.append(feature_state)
        elif (feature_segment := feature_state.feature_segment) is not None:
            resolved.segment_overrides.setdefault(
                feature_segment.segment_id, []
            ).append(feature_state)
        else:
            resolved.feature_states.append(feature_state)

    return resolved


def map_feature_state_to_feature_context(
    feature_state: "FeatureState",
    *,
    mv_fs_values: "Iterable[MultivariateFeatureStateValue] | None" = None,
    priority: float | None = None,
) -> FeatureContext:
    """Map a Django ORM FeatureState to a flag-engine FeatureContext TypedDict."""
    feature = feature_state.feature
    feature_context: FeatureContext = {
        # The engine seeds multivariate variant allocation on the feature
        # context key, so it has to be the bucketing seed rather than the
        # feature state id, or recreating a feature state would move every
        # enrolled identity to a different variant. See issue #7913.
        "key": str(feature_state.mv_hashing_seed),
        "name": feature.name,
        "enabled": feature_state.enabled,
        # Deliberately unparameterised by identity: picking a multivariate
        # value is the engine's job now.
        "value": feature_state.get_feature_state_value(),
        "metadata": FeatureEngineMetadata(feature_state=feature_state),
    }

    if variants := _map_mv_fs_values_to_feature_values(mv_fs_values or ()):
        feature_context["variants"] = variants

    if priority is not None:
        feature_context["priority"] = priority
    elif (feature_segment := feature_state.feature_segment) is not None:
        feature_context["priority"] = feature_segment.priority

    return feature_context


def _map_mv_fs_values_to_feature_values(
    mv_fs_values: "Iterable[MultivariateFeatureStateValue]",
) -> list[engine_types.FeatureValue]:
    # Ordered by id, and weighted by position in that order, because that is
    # the order Core API has always allocated percentages in. The engine
    # orders by `priority`, so the two only agree if we hand it the id order.
    feature_values: list[engine_types.FeatureValue] = []
    for index, mv_fs_value in enumerate(sorted(mv_fs_values, key=attrgetter("id"))):
        mv_option = mv_fs_value.multivariate_feature_option
        feature_value: engine_types.FeatureValue = {
            "value": mv_option.value,
            "weight": mv_fs_value.percentage_allocation,
            "priority": index,
        }
        if mv_option.key is not None:
            # An unkeyed option resolves to a null variant, as it does today.
            feature_value["key"] = mv_option.key
        feature_values.append(feature_value)
    return feature_values


def map_segment_to_segment_context(
    segment: "Segment",
    *,
    overrides: "list[FeatureContext] | None" = None,
) -> SegmentContext:
    """Map a Django ORM Segment to a flag-engine SegmentContext TypedDict."""
    segment_context: SegmentContext = {
        "key": str(segment.pk),
        "name": segment.name,
        "rules": [map_rule_to_segment_rule(rule) for rule in segment.rules.all()],
        "metadata": SegmentEngineMetadata(source="segment", pk=segment.pk),
    }
    if overrides:
        segment_context["overrides"] = overrides
    return segment_context


def _map_identity_overrides_to_segment_context(
    overrides: "list[FeatureContext]",
) -> SegmentContext:
    """Express identity overrides as a segment matching the current identity."""
    return {
        "key": IDENTITY_OVERRIDES_SEGMENT_KEY,
        "name": IDENTITY_OVERRIDES_SEGMENT_NAME,
        "rules": [
            {
                "type": "ALL",
                "conditions": [
                    {
                        "property": "$.identity.key",
                        "operator": IS_SET,
                        "value": "",
                    }
                ],
            }
        ],
        "overrides": overrides,
        "metadata": SegmentEngineMetadata(source="identity_overrides"),
    }


def map_rule_to_segment_rule(rule: "SegmentRule") -> engine_types.SegmentRule:
    return {
        "type": _rule_type_adapter.validate_python(rule.type),
        "conditions": [
            map_condition_to_segment_condition(condition)
            for condition in rule.conditions.all()
        ],
        "rules": [map_rule_to_segment_rule(sub_rule) for sub_rule in rule.rules.all()],
    }


def map_condition_to_segment_condition(
    condition: "Condition",
) -> engine_types.StrValueSegmentCondition:
    return {
        "property": condition.property or "",
        "operator": _condition_operator_adapter.validate_python(condition.operator),
        "value": condition.value or "",
    }
