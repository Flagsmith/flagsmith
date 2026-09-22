import jsonpath_rfc9535
from jsonpath_rfc9535.exceptions import JSONPathError
from jsonpath_rfc9535.segments import JSONPathChildSegment, JSONPathSegment
from jsonpath_rfc9535.selectors import NameSelector

from features.dependencies.models import SegmentFlagReference
from features.dependencies.types import DependencyEdge, FeatureName
from features.models import Feature
from segments.types import SegmentRule

_JSONPathStr = str


def map_rules_to_prerequisite_feature_names(
    rules: list[SegmentRule],
) -> dict[_JSONPathStr, FeatureName]:
    """Returns the feature names keyed by the condition $.flags JSONPath"""
    return {
        f"{rule_json_path}.conditions[{condition_index}]": feature_name
        for rule_json_path, rule in _get_rules_by_json_path(rules).items()
        for condition_index, condition in enumerate(rule["conditions"])
        if (condition_property := condition["property"])
        and (feature_name := _get_prerequisite_feature_name(condition_property))
        is not None
    }


def _get_rules_by_json_path(
    rules: list[SegmentRule],
) -> dict[_JSONPathStr, SegmentRule]:
    rules_by_json_path: dict[_JSONPathStr, SegmentRule] = {}
    for rule_index, rule in enumerate(rules):
        rule_json_path = f"$[{rule_index}]"
        rules_by_json_path[rule_json_path] = rule
        for nested_index, nested_rule in enumerate(rule.get("rules", [])):
            rules_by_json_path[f"{rule_json_path}.rules[{nested_index}]"] = nested_rule
    return rules_by_json_path


def _get_prerequisite_feature_name(condition_property: str) -> FeatureName | None:
    """Return the feature name a `$.flags.<feature>` condition points at, if it does."""
    # Because of historical decisions, `$['flags']` can be a trait.
    if not condition_property.startswith("$.flags"):
        return None
    try:
        query_segments = jsonpath_rfc9535.compile(condition_property).segments
    except JSONPathError:
        return None
    if len(query_segments) < 2 or _get_selected_name(query_segments[0]) != "flags":
        return None
    return _get_selected_name(query_segments[1])


def map_reference_to_dependency_edge(
    *,
    feature: Feature,
    reference: SegmentFlagReference,
) -> DependencyEdge:
    """Describe the feature's dependency the indexed `$.flags` condition makes up."""
    segment = reference.segment
    if (rules := segment.rules_data) is None:
        raise ValueError(f"Segment {segment.id} is referenced but has no rules.")
    return {
        "feature": {"id": feature.id, "name": feature.name},
        "prerequisite": {
            "id": reference.prerequisite_feature.id,
            "name": reference.prerequisite_feature.name,
        },
        "segment": {
            "id": segment.id,
            "name": segment.name,
            "rules": rules,
            "condition_json_path": reference.condition_json_path,
            "is_system": segment.is_system_segment,
        },
    }


def _get_selected_name(query_segment: JSONPathSegment) -> str | None:
    if (
        not isinstance(query_segment, JSONPathChildSegment)
        or len(query_segment.selectors) != 1
    ):
        return None
    selector = query_segment.selectors[0]
    return selector.name if isinstance(selector, NameSelector) else None
