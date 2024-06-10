import pytest
from flag_engine.segments.constants import EQUAL, PERCENTAGE_SPLIT

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

    # Check that the versioning is correct, since we'll testing
    # against it later in the test.
    assert segment.version == 1
    assert segment.version_of == segment

    parent_rule1 = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )
    parent_rule2 = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ANY_RULE
    )

    child_rule1 = SegmentRule.objects.create(
        rule=parent_rule1, type=SegmentRule.ANY_RULE
    )
    child_rule2 = SegmentRule.objects.create(
        rule=parent_rule1, type=SegmentRule.ALL_RULE
    )
    child_rule3 = SegmentRule.objects.create(
        rule=parent_rule2, type=SegmentRule.NONE_RULE
    )
    child_rule4 = SegmentRule.objects.create(
        rule=parent_rule2, type=SegmentRule.ALL_RULE
    )

    condition1 = Condition.objects.create(
        rule=parent_rule1,
        property="parent_rule1",
        operator=EQUAL,
        value="condition1",
        created_with_segment=True,
    )
    condition2 = Condition.objects.create(
        rule=parent_rule1,
        property="parent_rule1",
        operator=PERCENTAGE_SPLIT,
        value="0.1",
        created_with_segment=False,
    )

    condition3 = Condition.objects.create(
        rule=child_rule1,
        property="child_rule1",
        operator=EQUAL,
        value="condition3",
        created_with_segment=True,
    )
    Condition.objects.create(
        rule=child_rule2,
        property="child_rule2",
        operator=PERCENTAGE_SPLIT,
        value="0.2",
        created_with_segment=False,
    )
    Condition.objects.create(
        rule=child_rule2,
        property="child_rule2",
        operator=EQUAL,
        value="condition5",
        created_with_segment=False,
    )

    Condition.objects.create(
        rule=child_rule3,
        property="child_rule3",
        operator=EQUAL,
        value="condition6",
        created_with_segment=False,
    )

    Condition.objects.create(
        rule=child_rule4,
        property="child_rule4",
        operator=EQUAL,
        value="condition7",
        created_with_segment=True,
    )

    # When
    new_segment = segment.deep_clone()

    # Then
    assert new_segment.name == segment.name
    assert new_segment.description == segment.description
    assert new_segment.project == project
    assert new_segment.feature == feature
    assert new_segment.version == 1
    assert new_segment.version_of == segment

    assert segment.version == 2

    assert len(new_segment.rules.all()) == len(segment.rules.all()) == 2
    new_parent_rule1, new_parent_rule2 = list(new_segment.rules.all())

    assert new_parent_rule1.segment == new_segment
    assert new_parent_rule2.segment == new_segment
    assert new_parent_rule1.type == parent_rule1.type
    assert new_parent_rule2.type == parent_rule2.type

    assert len(new_parent_rule1.rules.all()) == len(parent_rule1.rules.all()) == 2
    assert len(new_parent_rule2.rules.all()) == len(parent_rule2.rules.all()) == 2
    new_child_rule1, new_child_rule2 = list(new_parent_rule1.rules.all())

    assert new_child_rule1.type == child_rule1.type
    assert new_child_rule2.type == child_rule2.type

    new_child_rule3, new_child_rule4 = list(new_parent_rule2.rules.all())

    assert new_child_rule3.type == child_rule3.type
    assert new_child_rule4.type == child_rule4.type

    assert (
        len(new_parent_rule1.conditions.all())
        == len(parent_rule1.conditions.all())
        == 2
    )

    new_condition1, new_condition2 = list(new_parent_rule1.conditions.all())

    assert new_condition1.property == condition1.property
    assert new_condition1.operator == condition1.operator
    assert new_condition1.value == condition1.value
    assert new_condition1.created_with_segment is condition1.created_with_segment

    assert new_condition2.property == condition2.property
    assert new_condition2.operator == condition2.operator
    assert new_condition2.value == condition2.value
    assert new_condition2.created_with_segment is condition2.created_with_segment

    assert (
        len(new_child_rule1.conditions.all()) == len(child_rule1.conditions.all()) == 1
    )
    new_condition3 = new_child_rule1.conditions.first()

    assert new_condition3.property == condition3.property
    assert new_condition3.operator == condition3.operator
    assert new_condition3.value == condition3.value
    assert new_condition3.created_with_segment is condition3.created_with_segment

    # Since the conditions have been asserted at multiple levels,
    # we leave the rest to basic size assertions.
    assert (
        len(new_child_rule2.conditions.all()) == len(child_rule2.conditions.all()) == 2
    )
    assert (
        len(new_child_rule3.conditions.all()) == len(child_rule3.conditions.all()) == 1
    )
    assert (
        len(new_child_rule4.conditions.all()) == len(child_rule4.conditions.all()) == 1
    )


def test_manager_returns_only_highest_version_of_segments(
    segment: Segment,
) -> None:
    # Given
    # The built-in segment fixture is pre-versioned already.
    assert segment.version == 2
    assert segment.version_of == segment

    new_segment = segment.deep_clone()
    assert new_segment.version == 2
    assert segment.version == 3

    # When
    queryset1 = Segment.objects.filter(id=new_segment.id)
    queryset2 = Segment.all_objects.filter(id=new_segment.id)
    queryset3 = Segment.objects.filter(id=segment.id)
    queryset4 = Segment.all_objects.filter(id=segment.id)

    # Then
    assert not queryset1.exists()
    assert queryset2.first() == new_segment
    assert queryset3.first() == segment
    assert queryset4.first() == segment


def test_deep_clone_of_segment_with_sub_rule(
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

    sub_rule = SegmentRule.objects.create(type=SegmentRule.ALL_RULE)

    # Parent rule with invalid sub rule.
    SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE, rule=sub_rule
    )

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
