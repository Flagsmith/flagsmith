from unittest.mock import PropertyMock

import pytest
from flag_engine.segments.constants import EQUAL, PERCENTAGE_SPLIT
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
