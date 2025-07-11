from typing import Any, Callable

import pytest
from flag_engine.segments.constants import EQUAL, PERCENTAGE_SPLIT
from pytest_mock import MockerFixture

from segments.models import Condition, Segment, SegmentRule
from segments.services import SegmentCloneService


def test_SegmentManager__returns_any_segment(
    segment: Segment,
) -> None:
    # When
    cloned_segment = SegmentCloneService(segment).deep_clone()

    # Then
    assert Segment.objects.get(id=cloned_segment.pk) == cloned_segment
    assert Segment.objects.get(id=segment.pk) == segment


def test_LiveSegmentManager__returns_only_highest_version_of_segments(
    segment: Segment,
) -> None:
    # Given
    # The built-in segment fixture is pre-versioned already.
    assert segment.version == 2
    assert segment.version_of == segment

    # When
    cloned_segment = SegmentCloneService(segment).deep_clone()

    # Then
    assert segment.version == 3
    assert cloned_segment.version == 2
    assert not Segment.live_objects.filter(id=cloned_segment.pk).exists()
    assert Segment.live_objects.get(id=segment.pk) == segment


def test_SegmentRule_get_segment__nested_rule__returns_parent_segment(
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


def test_Condition_get_create_log_message__created_with_segment__returns_none(
    mocker: MockerFixture,
    segment: Segment,
    segment_rule: SegmentRule,
) -> None:
    # Given
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=True,
    )

    # When
    mock_history_instance = mocker.MagicMock()
    msg = condition.get_create_log_message(mock_history_instance)

    # Then
    assert msg is None


def test_Condition_get_create_log_message__created_after_segment__returns_message(
    mocker: MockerFixture,
    segment: Segment,
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
    mock_history_instance = mocker.MagicMock()
    msg = condition.get_create_log_message(mock_history_instance)

    # Then
    assert msg == f"Condition added to segment '{segment.name}'."


def test_Condition_get_delete_log_message__returns_message(
    mocker: MockerFixture,
    segment: Segment,
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
    mock_history_instance = mocker.MagicMock()
    msg = condition.get_delete_log_message(mock_history_instance)

    # Then
    assert msg == f"Condition removed from segment '{segment.name}'."


@pytest.mark.parametrize(
    "delete",
    [
        lambda rule: rule.delete(),
        lambda rule: rule.hard_delete(),
    ],
)
def test_Condition_get_skip_create_audit_log__rule_deleted__returns_true(
    delete: Callable[[SegmentRule], None],
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
    delete(segment_rule)

    # Then
    assert condition.get_skip_create_audit_log() is True


@pytest.mark.parametrize(
    "delete",
    [
        lambda segment: segment.delete(),
        lambda segment: segment.hard_delete(),
    ],
)
def test_Condition_get_skip_create_audit_log__segment_deleted__returns_true(
    delete: Callable[[Segment], None],
    segment: Segment,
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
    delete(segment)

    # Then
    assert condition.get_skip_create_audit_log() is True


@pytest.mark.parametrize(
    "delete",
    [
        lambda segment: segment.delete(),
        lambda segment: segment.hard_delete(),
    ],
)
def test_Condition_get_delete_log_message__segment_deleted__returns_none(
    delete: Callable[[Segment], None],
    mocker: MockerFixture,
    segment: Segment,
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
    delete(segment)
    mock_history_instance = mocker.MagicMock()
    msg = condition.get_delete_log_message(mock_history_instance)

    # Then
    assert msg is None


def test_Condition_get_update_log_message__returns_message(
    mocker: MockerFixture,
    segment: Segment,
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
    mock_history_instance = mocker.MagicMock()
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
def test_Segment_id_exists_in_rules_data__checks_for_any_id(
    rules_data: list[dict[str, Any]],
    expected_result: bool,
) -> None:
    assert Segment.id_exists_in_rules_data(rules_data) == expected_result


@pytest.mark.parametrize(
    "delete",
    [
        lambda segment: segment.delete(),
        lambda segment: segment.hard_delete(),
    ],
)
def test_SegmentRule_get_skip_create_audit_log__segment_deleted__returns_true(
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


def test_SegmentRule_get_skip_create_audit_log__new_segment__returns_false(
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


def test_SegmentRule_get_skip_create_audit_log__segment_revision__returns_true(
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


def test_Segment_delete__multiple_rules_conditions__schedules_audit_log_task_once(
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
    task = mocker.patch("core.signals.tasks.create_audit_log_from_historical_record")
    segment.delete()

    # Then
    assert task.delay.call_count == 1
