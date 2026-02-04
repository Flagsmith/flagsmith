"""
Vendored and adapted mappers from flagsmith-flag-engine's fix/missing-export branch.

The original `map_environment_identity_to_context` function has been adapted to
return v10's EvaluationContext TypedDict instead of the original return type.
"""

import typing

from flag_engine.context.types import (
    EvaluationContext,
    FeatureContext,
    SegmentContext,
    SegmentRule,
)

from util.engine_models.features.models import (
    FeatureStateModel,
    MultivariateFeatureStateValueModel,
)
from util.engine_models.identities.models import IdentityModel
from util.engine_models.identities.traits.models import TraitModel
from util.engine_models.segments.models import SegmentModel, SegmentRuleModel


def map_environment_identity_to_context(
    environment: typing.Any,  # Accepts both Django Environment and Pydantic EnvironmentModel
    identity: IdentityModel,
    override_traits: typing.Optional[typing.List[TraitModel]],
) -> EvaluationContext:
    """
    Map an environment and IdentityModel to an EvaluationContext.

    Vendored from flagsmith-flag-engine's fix/missing-export branch and adapted
    to return v10's EvaluationContext TypedDict.

    This function uses duck typing - it only accesses `api_key` and `name`
    attributes from the environment, which exist on both Django Environment
    models and Pydantic EnvironmentModel objects.

    :param environment: The environment object (Django or Pydantic).
    :param identity: The identity model object (Pydantic IdentityModel).
    :param override_traits: A list of TraitModel objects, to be used in place of
        `identity.identity_traits` if provided.
    :return: An EvaluationContext containing the environment and identity.
    """
    return {
        "environment": {
            "key": environment.api_key,
            "name": environment.name or "",
        },
        "identity": {
            "identifier": identity.identifier,
            "key": str(identity.django_id or identity.composite_key),
            "traits": {
                trait.trait_key: trait.trait_value
                for trait in (
                    override_traits
                    if override_traits is not None
                    else identity.identity_traits
                )
            },
        },
    }


def _map_feature_states_to_feature_contexts(
    feature_states: typing.List[FeatureStateModel],
) -> typing.Dict[str, FeatureContext]:
    """
    Map feature states to feature contexts.

    :param feature_states: A list of FeatureStateModel objects.
    :return: A dictionary mapping feature names to their contexts.
    """
    features: typing.Dict[str, FeatureContext] = {}
    for feature_state in feature_states:
        feature_context: FeatureContext = {
            "key": str(feature_state.django_id or feature_state.featurestate_uuid),
            "name": feature_state.feature.name,
            "enabled": feature_state.enabled,
            "value": feature_state.feature_state_value,
        }
        multivariate_feature_state_values: typing.List[
            MultivariateFeatureStateValueModel
        ]
        if multivariate_feature_state_values := list(
            feature_state.multivariate_feature_state_values
        ):
            sorted_mv_values = sorted(
                multivariate_feature_state_values,
                key=_get_multivariate_feature_state_value_id,
            )
            feature_context["variants"] = [
                {
                    "value": mv_value.multivariate_feature_option.value,
                    "weight": mv_value.percentage_allocation,
                    "priority": idx,
                }
                for idx, mv_value in enumerate(sorted_mv_values)
            ]
        if feature_segment := feature_state.feature_segment:
            if (priority := feature_segment.priority) is not None:
                feature_context["priority"] = priority
        features[feature_state.feature.name] = feature_context
    return features


def _map_segment_rules_to_segment_context_rules(
    rules: typing.List[SegmentRuleModel],
) -> typing.List[SegmentRule]:
    """
    Map segment rules to segment rules for the evaluation context.

    :param rules: A list of SegmentRuleModel objects.
    :return: A list of SegmentRule objects.
    """
    return [
        {
            "type": rule.type,
            "conditions": [
                {
                    "property": condition.property_ or "",
                    "operator": condition.operator,
                    "value": condition.value or "",
                }
                for condition in rule.conditions
            ],
            "rules": _map_segment_rules_to_segment_context_rules(rule.rules),
        }
        for rule in rules
    ]


def _get_multivariate_feature_state_value_id(
    multivariate_feature_state_value: MultivariateFeatureStateValueModel,
) -> int:
    return (
        multivariate_feature_state_value.id
        or multivariate_feature_state_value.mv_fs_value_uuid.int
    )


def map_segment_to_segment_context(segment: SegmentModel) -> SegmentContext:
    """
    Map a SegmentModel Pydantic model to a SegmentContext TypedDict.

    :param segment: The SegmentModel object.
    :return: A SegmentContext TypedDict.
    """
    segment_ctx: SegmentContext = {
        "key": str(segment.id),
        "name": segment.name,
        "rules": _map_segment_rules_to_segment_context_rules(segment.rules),
    }
    if segment_feature_states := segment.feature_states:
        segment_ctx["overrides"] = list(
            _map_feature_states_to_feature_contexts(segment_feature_states).values()
        )
    return segment_ctx


def is_context_in_segment(
    context: EvaluationContext,
    segment: SegmentModel,
) -> bool:
    """
    Check if an evaluation context matches a segment.

    This is a compatibility wrapper that bridges the Pydantic SegmentModel
    with the v10 flag-engine's TypedDict-based evaluation API.

    :param context: The EvaluationContext (TypedDict).
    :param segment: The SegmentModel (Pydantic model).
    :return: True if the context matches the segment rules.
    """
    from flag_engine.segments.evaluator import (
        is_context_in_segment as v10_is_context_in_segment,
    )

    segment_context = map_segment_to_segment_context(segment)
    return v10_is_context_in_segment(context, segment_context)


def get_context_segments(
    context: EvaluationContext,
    segments: typing.List[SegmentModel],
) -> typing.List[SegmentModel]:
    """
    Get the list of segments that match a given evaluation context.

    This is a compatibility function for code that expects the old API.

    :param context: The EvaluationContext (TypedDict).
    :param segments: List of SegmentModel objects to check.
    :return: List of matching SegmentModel objects.
    """
    return [segment for segment in segments if is_context_in_segment(context, segment)]
