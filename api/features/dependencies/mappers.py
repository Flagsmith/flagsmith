import jsonpath_rfc9535
from jsonpath_rfc9535.exceptions import JSONPathError
from jsonpath_rfc9535.segments import JSONPathChildSegment, JSONPathSegment
from jsonpath_rfc9535.selectors import NameSelector

from features.dependencies.types import FeatureName, JSONPathStr
from segments.types import SegmentRule


def map_rules_to_prerequisite_feature_names(
    rules: list[SegmentRule],
) -> dict[JSONPathStr, FeatureName]:
    """Returns the feature names keyed by the condition $.flags JSONPath"""
    return {
        f"{rule_json_path}.conditions[{condition_index}]": feature_name
        for rule_json_path, rule in _get_rules_by_json_path(rules).items()
        for condition_index, condition in enumerate(rule["conditions"])
        if (condition_property := condition["property"])
        and (feature_name := _get_prerequisite_feature_name(condition_property))
    }


def _get_rules_by_json_path(
    rules: list[SegmentRule],
) -> dict[JSONPathStr, SegmentRule]:
    rules_by_json_path: dict[JSONPathStr, SegmentRule] = {}
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


def _get_selected_name(query_segment: JSONPathSegment) -> str | None:
    if (
        not isinstance(query_segment, JSONPathChildSegment)
        or len(query_segment.selectors) != 1
    ):
        return None
    selector = query_segment.selectors[0]
    return selector.name if isinstance(selector, NameSelector) else None
