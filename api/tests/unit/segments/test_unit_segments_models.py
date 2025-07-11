from typing import Callable

import pytest
from flag_engine.segments.constants import EQUAL, PERCENTAGE_SPLIT
from pytest_mock import MockerFixture

from segments.models import Condition, Segment, SegmentRule
from segments.services import SegmentCloneService


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


def test_condition_get_create_log_message_for_condition_created_with_segment(  # type: ignore[no-untyped-def]
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


def test_condition_get_create_log_message_for_condition_not_created_with_segment(  # type: ignore[no-untyped-def]
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


def test_condition_get_delete_log_message_for_valid_segment(  # type: ignore[no-untyped-def]
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


def test_condition_get_delete_log_message_for_deleted_segment(  # type: ignore[no-untyped-def]
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


def test_condition_get_update_log_message(segment, segment_rule, mocker):  # type: ignore[no-untyped-def]
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
def test_segment_id_exists_in_rules_data(rules_data, expected_result):  # type: ignore[no-untyped-def]
    assert Segment.id_exists_in_rules_data(rules_data) == expected_result


def test_manager_returns_only_highest_version_of_segments(
    segment: Segment,
) -> None:
    # Given
    # The built-in segment fixture is pre-versioned already.
    assert segment.version == 2
    assert segment.version_of == segment

    cloned_segment = SegmentCloneService(segment).deep_clone()
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


@pytest.mark.parametrize(
    "delete",
    [
        lambda segment: segment.delete(),
        lambda segment: segment.hard_delete(),
    ],
)
def test_segment_rule_get_skip_create_audit_log__skips_when_segment_deleted(
    segment: Segment,
    delete: Callable[[Segment], None],
) -> None:
    # Given
    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )

    # When
    delete(segment)

    # Then
    assert segment_rule.get_skip_create_audit_log() is True


def test_segment_rule_get_skip_create_audit_log__doesnt_skip_new_segment(
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


def test_segment_rule_get_skip_create_audit_log__skips_segment_revisions(
    segment: Segment,
) -> None:
    # Given
    cloned_segment = SegmentCloneService(segment).deep_clone()
    assert cloned_segment != cloned_segment.version_of
    segment_rule = SegmentRule.objects.create(
        segment=cloned_segment, type=SegmentRule.ALL_RULE
    )

    # When
    result = segment_rule.get_skip_create_audit_log()

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
