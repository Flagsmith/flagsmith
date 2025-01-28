from unittest.mock import PropertyMock

import pytest
from flag_engine.segments.constants import (
    EQUAL,
    GREATER_THAN,
    PERCENTAGE_SPLIT,
)
from pytest_mock import MockerFixture

from features.models import Feature
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule


def test_get_segment_returns_parent_segment_for_nested_rule(
    segment: Segment,
) -> None:
    # Given
    parent_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    child_rule = SegmentRule.objects.create(rule=parent_rule, type=SegmentRule.ALL_RULE)
    grandchild_rule = SegmentRule.objects.create(
        rule=child_rule, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(operator=PERCENTAGE_SPLIT, value=0.1, rule=grandchild_rule)

    # When
    new_segment = grandchild_rule.get_segment()

    # Then
    assert new_segment == segment


def test_condition_get_create_log_message_for_condition_created_with_segment(
    segment, segment_rule, mocker
):
    # Given
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=True,
    )

    mock_history_instance = mocker.MagicMock()

    # When
    msg = condition.get_create_log_message(mock_history_instance)

    # Then
    assert msg is None


def test_condition_get_create_log_message_for_condition_not_created_with_segment(
    segment, segment_rule, mocker
):
    # Given
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=False,
    )

    mock_history_instance = mocker.MagicMock()

    # When
    msg = condition.get_create_log_message(mock_history_instance)

    # Then
    assert msg == f"Condition added to segment '{segment.name}'."


def test_condition_get_delete_log_message_for_valid_segment(
    segment, segment_rule, mocker
):
    # Given
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=False,
    )

    mock_history_instance = mocker.MagicMock()

    # When
    msg = condition.get_delete_log_message(mock_history_instance)

    # Then
    assert msg == f"Condition removed from segment '{segment.name}'."


def test__condition_get_skip_create_audit_log_on_rule_delete(
    segment_rule: SegmentRule,
) -> None:
    # Given
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=False,
    )
    # When
    segment_rule.delete()

    # Then
    assert condition.get_skip_create_audit_log() is True


def test__condition_get_skip_create_audit_log_on_segment_delete(
    segment_rule: SegmentRule, segment: Segment
) -> None:
    # Given
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=False,
    )
    # When
    segment.delete()

    # Then
    assert condition.get_skip_create_audit_log() is True


def test__condition_get_skip_create_audit_log_on_segment_hard_delete(
    segment_rule: SegmentRule, segment: Segment
) -> None:
    # Given
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=False,
    )
    # When
    segment.delete()

    # Then
    assert condition.get_skip_create_audit_log() is True


def test_condition_get_delete_log_message_for_deleted_segment(
    segment, segment_rule, mocker
):
    # Given
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=False,
    )
    segment.delete()

    mock_history_instance = mocker.MagicMock()

    # When
    msg = condition.get_delete_log_message(mock_history_instance)

    # Then
    assert msg is None


def test_condition_get_update_log_message(segment, segment_rule, mocker):
    # Given
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=False,
    )

    mock_history_instance = mocker.MagicMock()

    # When
    msg = condition.get_update_log_message(mock_history_instance)

    # Then
    assert msg == f"Condition updated on segment '{segment.name}'."


@pytest.mark.parametrize(
    "rules_data, expected_result",
    (
        (
            [{"id": 1, "rules": [], "conditions": [], "type": SegmentRule.ALL_RULE}],
            True,
        ),
        ([{"rules": [], "conditions": [], "type": SegmentRule.ALL_RULE}], False),
        (
            [
                {
                    "rules": [
                        {
                            "id": 1,
                            "rules": [],
                            "conditions": [],
                            "type": SegmentRule.ALL_RULE,
                        }
                    ],
                    "conditions": [],
                    "type": SegmentRule.ALL_RULE,
                }
            ],
            True,
        ),
        (
            [
                {
                    "rules": [],
                    "conditions": [
                        {"id": 1, "property": "foo", "operator": EQUAL, "value": "bar"}
                    ],
                    "type": SegmentRule.ALL_RULE,
                }
            ],
            True,
        ),
    ),
)
def test_segment_id_exists_in_rules_data(rules_data, expected_result):
    assert Segment.id_exists_in_rules_data(rules_data) == expected_result


def test_deep_clone_of_segment(
    project: Project,
    feature: Feature,
) -> None:
    # Given
    segment = Segment.objects.create(
        name="SpecialSegment",
        description="A lovely, special segment.",
        project=project,
        feature=feature,
    )

    # Check that the versioning is correct, since we'll be testing
    # against it later in the test.
    assert segment.version == 1
    assert segment.version_of == segment

    parent_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

    child_rule1 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.ANY_RULE
    )
    child_rule2 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.NONE_RULE
    )
    child_rule3 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.NONE_RULE
    )
    child_rule4 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.ANY_RULE
    )

    condition1 = Condition.objects.create(
        rule=child_rule1,
        property="child_rule1",
        operator=EQUAL,
        value="condition3",
        created_with_segment=True,
    )
    condition2 = Condition.objects.create(
        rule=child_rule2,
        property="child_rule2",
        operator=PERCENTAGE_SPLIT,
        value="0.2",
        created_with_segment=False,
    )
    condition3 = Condition.objects.create(
        rule=child_rule2,
        property="child_rule2",
        operator=EQUAL,
        value="condition5",
        created_with_segment=False,
    )

    condition4 = Condition.objects.create(
        rule=child_rule3,
        property="child_rule3",
        operator=EQUAL,
        value="condition6",
        created_with_segment=False,
    )

    condition5 = Condition.objects.create(
        rule=child_rule4,
        property="child_rule4",
        operator=EQUAL,
        value="condition7",
        created_with_segment=True,
    )

    # When
    cloned_segment = segment.deep_clone()

    # Then
    assert cloned_segment.name == segment.name
    assert cloned_segment.description == segment.description
    assert cloned_segment.project == project
    assert cloned_segment.feature == feature
    assert cloned_segment.version == 1
    assert cloned_segment.version_of == segment

    assert segment.version == 2

    assert len(cloned_segment.rules.all()) == len(segment.rules.all()) == 1
    new_parent_rule = cloned_segment.rules.first()

    assert new_parent_rule.segment == cloned_segment
    assert new_parent_rule.type == parent_rule.type

    assert len(new_parent_rule.rules.all()) == len(parent_rule.rules.all()) == 4
    new_child_rule1, new_child_rule2, new_child_rule3, new_child_rule4 = list(
        new_parent_rule.rules.all()
    )

    assert new_child_rule1.type == child_rule1.type
    assert new_child_rule2.type == child_rule2.type
    assert new_child_rule3.type == child_rule3.type
    assert new_child_rule4.type == child_rule4.type

    assert (
        len(new_parent_rule.conditions.all()) == len(parent_rule.conditions.all()) == 0
    )

    assert (
        len(new_child_rule1.conditions.all()) == len(child_rule1.conditions.all()) == 1
    )
    new_condition1 = new_child_rule1.conditions.first()

    assert new_condition1.property == condition1.property
    assert new_condition1.operator == condition1.operator
    assert new_condition1.value == condition1.value
    assert new_condition1.created_with_segment is condition1.created_with_segment

    assert (
        len(new_child_rule2.conditions.all()) == len(child_rule2.conditions.all()) == 2
    )
    new_condition2, new_condition3 = list(new_child_rule2.conditions.all())

    assert new_condition2.property == condition2.property
    assert new_condition2.operator == condition2.operator
    assert new_condition2.value == condition2.value
    assert new_condition2.created_with_segment is condition2.created_with_segment

    assert new_condition3.property == condition3.property
    assert new_condition3.operator == condition3.operator
    assert new_condition3.value == condition3.value
    assert new_condition3.created_with_segment is condition3.created_with_segment

    assert (
        len(new_child_rule3.conditions.all()) == len(child_rule3.conditions.all()) == 1
    )
    new_condition4 = new_child_rule3.conditions.first()

    assert new_condition4.property == condition4.property
    assert new_condition4.operator == condition4.operator
    assert new_condition4.value == condition4.value
    assert new_condition4.created_with_segment is condition4.created_with_segment

    assert (
        len(new_child_rule4.conditions.all()) == len(child_rule4.conditions.all()) == 1
    )
    new_condition5 = new_child_rule4.conditions.first()

    assert new_condition5.property == condition5.property
    assert new_condition5.operator == condition5.operator
    assert new_condition5.value == condition5.value
    assert new_condition5.created_with_segment is condition5.created_with_segment


def test_manager_returns_only_highest_version_of_segments(
    segment: Segment,
) -> None:
    # Given
    # The built-in segment fixture is pre-versioned already.
    assert segment.version == 2
    assert segment.version_of == segment

    cloned_segment = segment.deep_clone()
    assert cloned_segment.version == 2
    assert segment.version == 3

    # When
    queryset1 = Segment.live_objects.filter(id=cloned_segment.id)
    queryset2 = Segment.objects.filter(id=cloned_segment.id)
    queryset3 = Segment.live_objects.filter(id=segment.id)
    queryset4 = Segment.objects.filter(id=segment.id)

    # Then
    assert not queryset1.exists()
    assert queryset2.first() == cloned_segment
    assert queryset3.first() == segment
    assert queryset4.first() == segment


def test_deep_clone_of_segment_with_improper_sub_rule(
    project: Project,
    feature: Feature,
) -> None:
    # Given
    segment = Segment.objects.create(
        name="SpecialSegment",
        description="A lovely, special segment.",
        project=project,
        feature=feature,
    )

    rule = SegmentRule.objects.create(
        type=SegmentRule.ALL_RULE,
        segment=segment,
    )

    # Rule with invalid relation to both segment and rule.
    SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE, rule=rule)

    with pytest.raises(AssertionError) as exception:
        segment.deep_clone()

    assert (
        "AssertionError: Unexpected rule, expecting segment set not rule"
        == exception.exconly()
    )


def test_deep_clone_of_segment_with_grandchild_rule(
    project: Project,
    feature: Feature,
) -> None:
    # Given
    segment = Segment.objects.create(
        name="SpecialSegment",
        description="A lovely, special segment.",
        project=project,
        feature=feature,
    )

    parent_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

    child_rule = SegmentRule.objects.create(rule=parent_rule, type=SegmentRule.ANY_RULE)

    # Grandchild rule, which is invalid
    SegmentRule.objects.create(rule=child_rule, type=SegmentRule.ANY_RULE)

    with pytest.raises(AssertionError) as exception:
        segment.deep_clone()

    assert (
        "AssertionError: Expected two layers of rules, not more" == exception.exconly()
    )


def test_segment_rule_get_skip_create_on_segment_hard_delete(
    segment: Segment,
) -> None:
    # Given
    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )

    # When
    segment.hard_delete()

    # Then
    assert segment_rule.get_skip_create_audit_log() is True


def test_segment_rule_get_skip_create_on_segment_delete(
    segment: Segment,
) -> None:
    # Given
    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )

    # When
    segment.delete()

    # Then
    assert segment_rule.get_skip_create_audit_log() is True


def test_segment_rule_get_skip_create_audit_log_when_doesnt_skip(
    segment: Segment,
) -> None:
    # Given
    assert segment == segment.version_of
    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )

    # When
    result = segment_rule.get_skip_create_audit_log()

    # Then
    assert result is False


def test_segment_rule_get_skip_create_audit_log_when_skips(segment: Segment) -> None:
    # Given
    cloned_segment = segment.deep_clone()
    assert cloned_segment != cloned_segment.version_of

    segment_rule = SegmentRule.objects.create(
        segment=cloned_segment, type=SegmentRule.ALL_RULE
    )

    # When
    result = segment_rule.get_skip_create_audit_log()

    # Then
    assert result is True


def test_segment_get_skip_create_audit_log_when_exception(
    mocker: MockerFixture,
    segment: Segment,
) -> None:
    # Given
    patched_segment = mocker.patch.object(
        Segment, "version_of_id", new_callable=PropertyMock
    )
    patched_segment.side_effect = Segment.DoesNotExist("Segment missing")

    # When
    result = segment.get_skip_create_audit_log()

    # Then
    assert result is True


def test_saving_rule_with_version_of_set(segment: Segment) -> None:
    # Given
    base_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    new_segment = Segment.objects.create(name="NewSegment", project=segment.project)

    # When
    rule = SegmentRule.objects.create(
        segment=new_segment, type=SegmentRule.ALL_RULE, version_of=base_rule
    )

    # Then
    assert rule.version_of == base_rule


def test_saving_condition_with_version_of_set(segment: Segment) -> None:
    # Given
    rule1 = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    new_segment = Segment.objects.create(name="NewSegment", project=segment.project)
    rule2 = SegmentRule.objects.create(
        segment=new_segment, type=SegmentRule.ALL_RULE, version_of=rule1
    )
    condition1 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.1, rule=rule1
    )

    # When
    condition2 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.1, rule=rule2, version_of=condition1
    )

    # Then
    assert condition2.version_of == condition1


def test_update_segment_with_matches_from_current_segment_with_two_levels_of_rules_and_two_conditions(
    project: Project,
) -> None:
    # Given
    # First we create our two segments, one that will be assign from the other.
    segment1 = Segment.objects.create(name="Segment1", project=project)
    segment2 = Segment.objects.create(name="Segment2", project=project)

    # Next we create two parent rules, both with the same type and then two
    # matching subrules, both with matching types as well.
    rule1 = SegmentRule.objects.create(segment=segment1, type=SegmentRule.ALL_RULE)
    rule2 = SegmentRule.objects.create(segment=segment2, type=SegmentRule.ALL_RULE)
    rule3 = SegmentRule.objects.create(rule=rule1, type=SegmentRule.ALL_RULE)
    rule4 = SegmentRule.objects.create(rule=rule2, type=SegmentRule.ALL_RULE)

    # Finally we create the conditions associated with the subrules with different
    # values set between them and a missing description on the second condition.
    condition1 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.1, rule=rule3, description="SomeDescription"
    )
    condition2 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.2, rule=rule4
    )
    # When
    segment1.update_segment_with_matches_from_current_segment(segment2)

    # Then
    rule1.refresh_from_db()
    rule2.refresh_from_db()
    rule3.refresh_from_db()
    rule4.refresh_from_db()
    condition1.refresh_from_db()
    condition2.refresh_from_db()

    # Now we see that the rules and conditions match for the segment that was
    # assigned to, since the condition matching logic allowed the rules to match
    # as well.
    assert rule1.version_of == rule2
    assert rule2.version_of is None
    assert rule3.version_of == rule4
    assert rule4.version_of is None
    assert condition1.version_of == condition2
    assert condition2.version_of is None


def test_update_segment_with_matches_from_current_segment_with_condition_operator_mismatch(
    project: Project,
) -> None:
    # Given
    # First we create our two segments, one that will be assign from the other.
    segment1 = Segment.objects.create(name="Segment1", project=project)
    segment2 = Segment.objects.create(name="Segment2", project=project)

    # Next we create two parent rules, both with the same type and then two
    # matching subrules, both with matching types as well.
    rule1 = SegmentRule.objects.create(segment=segment1, type=SegmentRule.ALL_RULE)
    rule2 = SegmentRule.objects.create(segment=segment2, type=SegmentRule.ALL_RULE)
    rule3 = SegmentRule.objects.create(rule=rule1, type=SegmentRule.ALL_RULE)
    rule4 = SegmentRule.objects.create(rule=rule2, type=SegmentRule.ALL_RULE)

    # Finally we create conditions that have matching property names with
    # mismatched operators so the frontend will be able to diff even when
    # a condition's operator is different.
    condition1 = Condition.objects.create(
        property="scale",
        operator=EQUAL,
        value=0.1,
        rule=rule3,
        description="Setting scale to equal",
    )
    condition2 = Condition.objects.create(
        property="scale",
        operator=GREATER_THAN,
        value=0.2,
        rule=rule4,
        description="Setting scale to greater than",
    )

    # When
    segment1.update_segment_with_matches_from_current_segment(segment2)

    # Then
    rule1.refresh_from_db()
    rule2.refresh_from_db()
    rule3.refresh_from_db()
    rule4.refresh_from_db()
    condition1.refresh_from_db()
    condition2.refresh_from_db()
    # The parent rule and subrule of the target segment match
    assert rule1.version_of == rule2
    assert rule2.version_of is None
    assert rule3.version_of == rule4
    assert rule4.version_of is None
    # The condition with the mismatched operator matches.
    assert condition1.version_of == condition2
    assert condition2.version_of is None


def test_update_segment_with_matches_from_current_segment_with_conditions_not_matching(
    project: Project,
) -> None:
    # Given
    # First we create our two segments, one that will be assign from the other.
    segment1 = Segment.objects.create(name="Segment1", project=project)
    segment2 = Segment.objects.create(name="Segment2", project=project)

    # Next we create two parent rules, both with the same type and then two
    # matching subrules, both with matching types as well.
    rule1 = SegmentRule.objects.create(segment=segment1, type=SegmentRule.ALL_RULE)
    rule2 = SegmentRule.objects.create(segment=segment2, type=SegmentRule.ALL_RULE)
    rule3 = SegmentRule.objects.create(rule=rule1, type=SegmentRule.ALL_RULE)
    rule4 = SegmentRule.objects.create(rule=rule2, type=SegmentRule.ALL_RULE)

    # Finally we create conditions that have mis-matched property names so
    # the frontend will not to be able to diff them since there will be no match
    condition1 = Condition.objects.create(
        property="age",
        operator=EQUAL,
        value=21,
        rule=rule3,
        description="Setting age to equal",
    )
    condition2 = Condition.objects.create(
        property="scale",
        operator=GREATER_THAN,
        value=0.2,
        rule=rule4,
        description="Setting scale to greater than",
    )

    # When
    segment1.update_segment_with_matches_from_current_segment(segment2)

    # Then
    rule1.refresh_from_db()
    rule2.refresh_from_db()
    rule3.refresh_from_db()
    rule4.refresh_from_db()
    condition1.refresh_from_db()
    condition2.refresh_from_db()
    # The parent rule and subrule of the target segments do not match.
    assert rule1.version_of is None
    assert rule2.version_of is None
    assert rule3.version_of is None
    assert rule4.version_of is None
    # The condition with the mismatched property also doesn't match.
    assert condition1.version_of is None
    assert condition2.version_of is None


def test_update_segment_with_matches_from_current_segment_mismatched_rule_type(
    project: Project,
) -> None:
    # Given
    # First we create our two segments, one that will be assign from the other.
    segment1 = Segment.objects.create(name="Segment1", project=project)
    segment2 = Segment.objects.create(name="Segment2", project=project)

    # Next we create parent rules with mismatched types with subrules with
    # matching subrule types.
    rule1 = SegmentRule.objects.create(segment=segment1, type=SegmentRule.ALL_RULE)
    rule2 = SegmentRule.objects.create(segment=segment2, type=SegmentRule.NONE_RULE)
    rule3 = SegmentRule.objects.create(rule=rule1, type=SegmentRule.ALL_RULE)
    rule4 = SegmentRule.objects.create(rule=rule2, type=SegmentRule.ALL_RULE)

    # We next create matching conditions.
    condition1 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.1, rule=rule3, description="SomeDescription"
    )
    condition2 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.2, rule=rule4
    )
    # When
    segment1.update_segment_with_matches_from_current_segment(segment2)

    # Then
    rule1.refresh_from_db()
    rule2.refresh_from_db()
    rule3.refresh_from_db()
    rule4.refresh_from_db()
    condition1.refresh_from_db()
    condition2.refresh_from_db()
    # Note that none of the rules or conditions matched because the parent rule
    # had a mismatched type so the entire collection is skipped.
    assert rule1.version_of is None
    assert rule2.version_of is None
    assert rule3.version_of is None
    assert rule4.version_of is None
    assert condition1.version_of is None
    assert condition2.version_of is None


def test_update_segment_with_matches_from_current_segment_mismatched_sub_rule_type(
    project: Project,
) -> None:
    # Given
    # First we create our two segments, one that will be assign from the other.
    segment1 = Segment.objects.create(name="Segment1", project=project)
    segment2 = Segment.objects.create(name="Segment2", project=project)

    # Next we create matching parent rules (based on type) and mismatched
    # subrules which have different types.
    rule1 = SegmentRule.objects.create(segment=segment1, type=SegmentRule.ALL_RULE)
    rule2 = SegmentRule.objects.create(segment=segment2, type=SegmentRule.ALL_RULE)
    rule3 = SegmentRule.objects.create(rule=rule1, type=SegmentRule.NONE_RULE)
    rule4 = SegmentRule.objects.create(rule=rule2, type=SegmentRule.ALL_RULE)

    # Finally we create matching conditions.
    condition1 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.1, rule=rule3, description="SomeDescription"
    )
    condition2 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.2, rule=rule4
    )
    # When
    segment1.update_segment_with_matches_from_current_segment(segment2)

    # Then
    rule1.refresh_from_db()
    rule2.refresh_from_db()
    rule3.refresh_from_db()
    rule4.refresh_from_db()
    condition1.refresh_from_db()
    condition2.refresh_from_db()
    # See that since the subrules didn't match none of the collection is
    # assigned to be a version_of.
    assert rule1.version_of is None
    assert rule2.version_of is None
    assert rule3.version_of is None
    assert rule4.version_of is None
    assert condition1.version_of is None
    assert condition2.version_of is None


def test_update_segment_with_matches_from_current_segment_multiple_sub_rules(
    project: Project,
) -> None:
    # Given
    # First we create our two segments, one that will be assign from the other.
    segment1 = Segment.objects.create(name="Segment1", project=project)
    segment2 = Segment.objects.create(name="Segment2", project=project)

    # Next we create two parent rules for each segment.
    rule1 = SegmentRule.objects.create(segment=segment1, type=SegmentRule.ALL_RULE)
    rule2 = SegmentRule.objects.create(segment=segment1, type=SegmentRule.ALL_RULE)
    rule3 = SegmentRule.objects.create(segment=segment2, type=SegmentRule.ALL_RULE)
    rule4 = SegmentRule.objects.create(segment=segment2, type=SegmentRule.ALL_RULE)

    # We assign two rules to the first parent rule.
    rule5 = SegmentRule.objects.create(rule=rule1, type=SegmentRule.ALL_RULE)
    rule6 = SegmentRule.objects.create(rule=rule1, type=SegmentRule.ALL_RULE)

    # We assign two rules to the second parent rule.
    rule7 = SegmentRule.objects.create(rule=rule2, type=SegmentRule.ALL_RULE)
    rule8 = SegmentRule.objects.create(rule=rule2, type=SegmentRule.ALL_RULE)

    # We assign one rule to the third parent rule and two rules to the fourth
    # parent rule.
    rule9 = SegmentRule.objects.create(rule=rule3, type=SegmentRule.ALL_RULE)
    rule10 = SegmentRule.objects.create(rule=rule4, type=SegmentRule.ALL_RULE)
    rule11 = SegmentRule.objects.create(rule=rule4, type=SegmentRule.ALL_RULE)

    # When
    segment1.update_segment_with_matches_from_current_segment(segment2)

    # Then
    rule1.refresh_from_db()
    rule2.refresh_from_db()
    rule3.refresh_from_db()
    rule4.refresh_from_db()
    rule5.refresh_from_db()
    rule6.refresh_from_db()
    rule7.refresh_from_db()
    rule8.refresh_from_db()
    rule9.refresh_from_db()
    rule10.refresh_from_db()

    # First we verify that the two parent rules match each other.
    assert rule1.version_of == rule3
    assert rule2.version_of == rule4

    # Next we verify that the non-targeted parent rules are not assigned.
    assert rule3.version_of is None
    assert rule4.version_of is None

    # Lastly we verify that our subrules are assigned to their proper targets.
    assert rule5.version_of == rule9
    assert rule6.version_of is None
    assert rule7.version_of == rule10
    assert rule8.version_of == rule11
    assert rule9.version_of is None
    assert rule10.version_of is None
    assert rule11.version_of is None


def test_update_segment_with_matches_from_current_segment_with_multiple_conditions(
    project: Project,
) -> None:
    # Given
    # First we create our two segments, one that will be assign from the other.
    segment1 = Segment.objects.create(name="Segment1", project=project)
    segment2 = Segment.objects.create(name="Segment2", project=project)

    # Next we create the parent rules for the segments and each with one subrule.
    rule1 = SegmentRule.objects.create(segment=segment1, type=SegmentRule.ALL_RULE)
    rule2 = SegmentRule.objects.create(segment=segment2, type=SegmentRule.ALL_RULE)
    rule3 = SegmentRule.objects.create(rule=rule1, type=SegmentRule.ALL_RULE)
    rule4 = SegmentRule.objects.create(rule=rule2, type=SegmentRule.ALL_RULE)

    # Lastly we create two sets of conditions per subrule with matching conditions.
    condition1 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.1, rule=rule3, description="SomeDescription"
    )
    condition2 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.2, rule=rule3
    )
    condition3 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.3, rule=rule4
    )
    condition4 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.4, rule=rule4
    )
    # When
    segment1.update_segment_with_matches_from_current_segment(segment2)

    # Then
    rule1.refresh_from_db()
    rule2.refresh_from_db()
    rule3.refresh_from_db()
    rule4.refresh_from_db()
    condition1.refresh_from_db()
    condition2.refresh_from_db()
    condition3.refresh_from_db()
    condition4.refresh_from_db()

    # Now the parent rule (rule1) is set to the other parent rule and the
    # subrule (rule3) is set to the other subrule with both conditions
    # set to their matching conditions from the other subrule.
    assert rule1.version_of == rule2
    assert rule2.version_of is None
    assert rule3.version_of == rule4
    assert rule4.version_of is None
    assert condition1.version_of == condition3
    assert condition2.version_of == condition4
    assert condition3.version_of is None
    assert condition4.version_of is None


def test_update_segment_with_matches_from_current_segment_with_exact_condition_match(
    project: Project,
) -> None:
    # Given
    # First we create our two segments, one that will be assign from the other.
    segment1 = Segment.objects.create(name="Segment1", project=project)
    segment2 = Segment.objects.create(name="Segment2", project=project)

    # Next we create the parent rules for the segments and each with one subrule.
    rule1 = SegmentRule.objects.create(segment=segment1, type=SegmentRule.ALL_RULE)
    rule2 = SegmentRule.objects.create(segment=segment2, type=SegmentRule.ALL_RULE)
    rule3 = SegmentRule.objects.create(rule=rule1, type=SegmentRule.ALL_RULE)
    rule4 = SegmentRule.objects.create(rule=rule2, type=SegmentRule.ALL_RULE)

    # Lastly we create a number of conditions to attempt matching to, with an exact
    # matching condition present.
    condition1 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT,
        value=0.1,
        rule=rule3,
    )
    condition2 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.2, rule=rule4
    )
    condition3 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.1, rule=rule4
    )
    condition4 = Condition.objects.create(
        operator=PERCENTAGE_SPLIT, value=0.4, rule=rule4
    )
    # When
    segment1.update_segment_with_matches_from_current_segment(segment2)

    # Then
    rule1.refresh_from_db()
    rule2.refresh_from_db()
    rule3.refresh_from_db()
    rule4.refresh_from_db()
    condition1.refresh_from_db()
    condition2.refresh_from_db()
    condition3.refresh_from_db()
    condition4.refresh_from_db()

    # Now the parent rule (rule1) is set to the other parent rule and the
    # subrule (rule3) is set to the other subrule with the exact
    # matching conditions being set.
    assert rule1.version_of == rule2
    assert rule2.version_of is None
    assert rule3.version_of == rule4
    assert rule4.version_of is None
    assert condition1.version_of == condition3
    assert condition2.version_of is None
    assert condition3.version_of is None
    assert condition4.version_of is None


def test_delete_segment_only_schedules_one_task_for_audit_log_creation(
    mocker: MockerFixture, segment: Segment
) -> None:
    # Given
    for _ in range(5):
        segment_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        for _ in range(5):
            Condition.objects.create(
                rule=segment_rule,
                property="foo",
                operator=EQUAL,
                value="bar",
                created_with_segment=False,
            )

    # When
    mocked_tasks = mocker.patch("core.signals.tasks")
    segment.delete()

    # Then
    assert len(mocked_tasks.mock_calls) == 1
