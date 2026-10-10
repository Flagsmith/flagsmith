import typing
from typing import Any

from simple_history.models import ModelChange

if typing.TYPE_CHECKING:
    from segments.models import Condition, Segment, SegmentRule


def get_segment_rules_data(segment: "Segment") -> list[dict[str, Any]]:
    """
    Serialize a segment's rules and conditions into a list of dicts
    suitable for comparison in audit log change details.
    """
    from segments.models import Condition, SegmentRule

    top_level_rules = list(SegmentRule.objects.filter(segment=segment).order_by("id"))
    if not top_level_rules:
        return []

    # Collect all rule IDs level by level.
    rule_id_to_children: dict[int, list["SegmentRule"]] = {}
    current_level = top_level_rules

    while current_level:
        current_ids = [r.id for r in current_level]
        nested = list(
            SegmentRule.objects.filter(rule_id__in=current_ids).order_by("id")
        )
        for rule in nested:
            parent_id: int = rule.rule_id  # type: ignore[assignment]
            rule_id_to_children.setdefault(parent_id, []).append(rule)
        current_level = nested

    # Collect all conditions in one query.
    all_rule_ids: set[int] = set()
    _collect_rule_ids(top_level_rules, rule_id_to_children, all_rule_ids)
    conditions = list(Condition.objects.filter(rule_id__in=all_rule_ids).order_by("id"))
    rule_id_to_conditions: dict[int, list["Condition"]] = {}
    for condition in conditions:
        cond_rule_id: int = condition.rule_id
        rule_id_to_conditions.setdefault(cond_rule_id, []).append(condition)

    return [
        _serialize_rule(rule, rule_id_to_children, rule_id_to_conditions)
        for rule in top_level_rules
    ]


def _collect_rule_ids(
    rules: list[Any],
    rule_id_to_children: dict[int, list[Any]],
    result: set[int],
) -> None:
    for rule in rules:
        result.add(rule.id)
        children = rule_id_to_children.get(rule.id, [])
        _collect_rule_ids(children, rule_id_to_children, result)


def _serialize_rule(
    rule: "SegmentRule",
    rule_id_to_children: dict[int, list[Any]],
    rule_id_to_conditions: dict[int, list[Any]],
) -> dict[str, Any]:
    conditions = rule_id_to_conditions.get(rule.id, [])
    children = rule_id_to_children.get(rule.id, [])
    data: dict[str, Any] = {"type": rule.type}
    if conditions:
        data["conditions"] = [_serialize_condition(c) for c in conditions]
    if children:
        data["rules"] = [
            _serialize_rule(child, rule_id_to_children, rule_id_to_conditions)
            for child in children
        ]
    return data


def _serialize_condition(condition: "Condition") -> dict[str, Any]:
    data: dict[str, Any] = {
        "operator": condition.operator,
    }
    if condition.property:
        data["property"] = condition.property
    if condition.value is not None:
        data["value"] = condition.value
    return data


def get_segment_rules_change_details(
    segment_id: int,
    current_version: int,
) -> list[ModelChange]:
    """
    Compute rule change details for a segment update by comparing
    the previous revision's rules against the current version's rules.

    Uses revision records for both old and new state so that historical
    audit entries remain accurate even after further updates.

    Only called from the retrieve serializer (single object), not the
    list endpoint, so the extra queries are bounded.
    """
    from segments.models import Segment

    # The "old" state is the revision with version = current_version - 1.
    previous_revision = (
        Segment.objects.filter(
            version_of_id=segment_id,
            version=current_version - 1,
        )
        .order_by("-id")
        .first()
    )

    if previous_revision is None:
        return []

    # The "new" state: look for a revision that captured this version
    # (created by the next update). If none exists, the live segment
    # is still at this version and we use it directly.
    current_revision = (
        Segment.objects.filter(
            version_of_id=segment_id,
            version=current_version,
        )
        .order_by("-id")
        .first()
    )

    if current_revision is None:
        # This is the latest update; use the live segment.
        try:
            current_segment = Segment.objects.get(id=segment_id)
        except Segment.DoesNotExist:
            return []
        new_rules = get_segment_rules_data(current_segment)
    else:
        new_rules = get_segment_rules_data(current_revision)

    old_rules = get_segment_rules_data(previous_revision)

    if old_rules == new_rules:
        return []

    return [
        ModelChange(
            "rules",
            _format_rules_for_display(old_rules),
            _format_rules_for_display(new_rules),
        )
    ]


def _format_rules_for_display(rules_data: list[dict[str, Any]]) -> str:
    """Format rules data into a human-readable string for the audit log."""
    if not rules_data:
        return "(empty)"

    parts = []
    for rule in rules_data:
        parts.append(_format_rule(rule))
    return "; ".join(parts)


def _format_rule(rule: dict[str, Any]) -> str:
    rule_type = rule["type"]
    conditions: list[dict[str, Any]] = rule.get("conditions", [])
    sub_rules: list[dict[str, Any]] = rule.get("rules", [])

    condition_strs = []
    for c in conditions:
        prop = c.get("property", "")
        op = c["operator"]
        val = c.get("value", "")
        condition_strs.append(f"{prop} {op} {val}".strip())

    sub_rule_strs = [_format_rule(r) for r in sub_rules]

    all_parts = condition_strs + sub_rule_strs
    if not all_parts:
        return f"{rule_type}()"

    joiner = f" {rule_type} "
    return f"({joiner.join(all_parts)})"
