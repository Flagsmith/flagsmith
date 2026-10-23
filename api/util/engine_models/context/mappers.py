"""
Vendored and adapted mappers from flagsmith-flag-engine's fix/missing-export branch.

The original `map_environment_identity_to_context` function has been adapted to
return v10's EvaluationContext TypedDict instead of the original return type.
"""

import typing

from flag_engine.context.types import (
    FeatureContext,
    SegmentContext,
    SegmentRule,
)

from util.engine_models.features.models import (
    FeatureStateModel,
    MultivariateFeatureStateValueModel,
)
from util.engine_models.segments.models import SegmentModel, SegmentRuleModel


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
