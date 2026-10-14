from flag_engine.segments.constants import EQUAL, GREATER_THAN

from segments.audit_helpers import (
    _format_rules_for_display,
    get_segment_rules_change_details,
    get_segment_rules_data,
)
from segments.models import Condition, Segment, SegmentRule


def test_get_segment_rules_data__no_rules__returns_empty_list(
    segment: Segment,
) -> None:
    # Given - segment with no rules
    # When
    result = get_segment_rules_data(segment)
    # Then
    assert result == []


def test_get_segment_rules_data__single_rule__returns_serialized_conditions(
    segment: Segment,
) -> None:
    # Given
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, operator=EQUAL, property="age", value="25")

    # When
    result = get_segment_rules_data(segment)

    # Then
    assert result == [
        {
            "type": "ALL",
            "conditions": [{"operator": EQUAL, "property": "age", "value": "25"}],
        }
    ]


def test_get_segment_rules_data__nested_rules__returns_nested_structure(
    segment: Segment,
) -> None:
    # Given
    top_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    nested_rule = SegmentRule.objects.create(rule=top_rule, type=SegmentRule.ANY_RULE)
    Condition.objects.create(
        rule=nested_rule, operator=EQUAL, property="country", value="US"
    )
    Condition.objects.create(
        rule=nested_rule, operator=EQUAL, property="country", value="UK"
    )

    # When
    result = get_segment_rules_data(segment)

    # Then
    assert result == [
        {
            "type": "ALL",
            "rules": [
                {
                    "type": "ANY",
                    "conditions": [
                        {"operator": EQUAL, "property": "country", "value": "US"},
                        {"operator": EQUAL, "property": "country", "value": "UK"},
                    ],
                }
            ],
        }
    ]


def test_get_segment_rules_data__multiple_top_rules__returns_all_rules(
    segment: Segment,
) -> None:
    # Given
    rule1 = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    rule2 = SegmentRule.objects.create(segment=segment, type=SegmentRule.ANY_RULE)
    Condition.objects.create(rule=rule1, operator=EQUAL, property="plan", value="pro")
    Condition.objects.create(
        rule=rule2, operator=GREATER_THAN, property="age", value="18"
    )

    # When
    result = get_segment_rules_data(segment)

    # Then
    assert len(result) == 2
    assert result[0]["type"] == "ALL"
    assert result[0]["conditions"] == [
        {"operator": EQUAL, "property": "plan", "value": "pro"}
    ]
    assert result[1]["type"] == "ANY"
    assert result[1]["conditions"] == [
        {"operator": GREATER_THAN, "property": "age", "value": "18"}
    ]


def test_get_segment_rules_data__no_property_condition__omits_property_key(
    segment: Segment,
) -> None:
    # Given - percentage split condition has no property
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, operator="PERCENTAGE_SPLIT", value="50")

    # When
    result = get_segment_rules_data(segment)

    # Then
    assert result == [
        {
            "type": "ALL",
            "conditions": [{"operator": "PERCENTAGE_SPLIT", "value": "50"}],
        }
    ]


def test_get_segment_rules_change_details__rules_changed__returns_diff(
    project,
) -> None:
    # Given
    segment = Segment.objects.create(name="test", project=project)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, operator=EQUAL, property="age", value="25")
    segment.clone(is_revision=True)

    Condition.objects.filter(rule__segment=segment).delete()
    SegmentRule.objects.filter(segment=segment).delete()
    new_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=new_rule, operator=GREATER_THAN, property="age", value="30"
    )

    # When
    result = get_segment_rules_change_details(
        segment_id=segment.id,
        current_version=segment.version,
    )

    # Then
    assert len(result) == 1
    assert result[0].field == "rules"
    assert "age EQUAL 25" in result[0].old
    assert "age GREATER_THAN 30" in result[0].new


def test_get_segment_rules_change_details__rules_unchanged__returns_empty_list(
    project,
) -> None:
    # Given
    segment = Segment.objects.create(name="test", project=project)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, operator=EQUAL, property="age", value="25")
    segment.clone(is_revision=True)

    # When
    result = get_segment_rules_change_details(
        segment_id=segment.id,
        current_version=segment.version,
    )

    # Then
    assert result == []


def test_get_segment_rules_change_details__no_previous_revision__returns_empty_list(
    project,
) -> None:
    # Given
    segment = Segment.objects.create(name="test", project=project)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, operator=EQUAL, property="age", value="25")

    # When
    result = get_segment_rules_change_details(
        segment_id=segment.id,
        current_version=1,
    )

    # Then
    assert result == []


def test_get_segment_rules_change_details__segment_deleted__returns_empty_list(
    project,
) -> None:
    # Given - non-existent segment
    # When
    result = get_segment_rules_change_details(
        segment_id=99999,
        current_version=2,
    )

    # Then
    assert result == []


def test_get_segment_rules_change_details__two_updates__shows_correct_diff_for_first(
    project,
) -> None:
    # Given - segment updated twice
    segment = Segment.objects.create(name="test", project=project)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, operator=EQUAL, property="age", value="25")

    # First update: rules change from [age=25] to [age=30]
    segment.clone(is_revision=True)
    Condition.objects.filter(rule__segment=segment).delete()
    SegmentRule.objects.filter(segment=segment).delete()
    rule2 = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=rule2, operator=GREATER_THAN, property="age", value="30"
    )
    first_update_version = segment.version  # version=2

    # Second update: rules change from [age>30] to [plan=pro]
    segment.clone(is_revision=True)
    Condition.objects.filter(rule__segment=segment).delete()
    SegmentRule.objects.filter(segment=segment).delete()
    rule3 = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule3, operator=EQUAL, property="plan", value="pro")
    second_update_version = segment.version  # version=3

    # When - check the diff for the FIRST update
    result_first = get_segment_rules_change_details(
        segment_id=segment.id,
        current_version=first_update_version,
    )

    # Then - should show [age=25] -> [age>30], NOT [age=25] -> [plan=pro]
    assert len(result_first) == 1
    assert "age EQUAL 25" in result_first[0].old
    assert "age GREATER_THAN 30" in result_first[0].new
    assert "plan" not in result_first[0].new

    # When - check the diff for the SECOND update
    result_second = get_segment_rules_change_details(
        segment_id=segment.id,
        current_version=second_update_version,
    )

    # Then - should show [age>30] -> [plan=pro]
    assert len(result_second) == 1
    assert "age GREATER_THAN 30" in result_second[0].old
    assert "plan EQUAL pro" in result_second[0].new


def test_format_rules_for_display__empty_rules__returns_empty_marker() -> None:
    # Given
    rules: list = []

    # When
    result = _format_rules_for_display(rules)

    # Then
    assert result == "(empty)"


def test_format_rules_for_display__single_condition__returns_flat_expression() -> None:
    # Given
    rules = [
        {
            "type": "ALL",
            "conditions": [{"operator": "EQUAL", "property": "x", "value": "1"}],
        }
    ]

    # When
    result = _format_rules_for_display(rules)

    # Then
    assert result == "(x EQUAL 1)"


def test_format_rules_for_display__multiple_conditions__joins_with_type() -> None:
    # Given
    rules = [
        {
            "type": "ALL",
            "conditions": [
                {"operator": "EQUAL", "property": "x", "value": "1"},
                {"operator": "GREATER_THAN", "property": "y", "value": "2"},
            ],
        }
    ]

    # When
    result = _format_rules_for_display(rules)

    # Then
    assert result == "(x EQUAL 1 ALL y GREATER_THAN 2)"


def test_format_rules_for_display__nested_rules__returns_nested_parentheses() -> None:
    # Given
    rules = [
        {
            "type": "ALL",
            "rules": [
                {
                    "type": "ANY",
                    "conditions": [
                        {"operator": "EQUAL", "property": "a", "value": "1"},
                        {"operator": "EQUAL", "property": "b", "value": "2"},
                    ],
                }
            ],
        }
    ]

    # When
    result = _format_rules_for_display(rules)

    # Then
    assert result == "((a EQUAL 1 ANY b EQUAL 2))"
