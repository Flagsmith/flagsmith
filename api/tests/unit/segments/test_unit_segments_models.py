from collections.abc import Callable
from typing import Any
from unittest.mock import PropertyMock

import pytest
from django.core.exceptions import ValidationError
from flag_engine.segments.constants import EQUAL
from pytest_mock import MockerFixture

from segments.models import Condition, Segment, SegmentRule


def test_Condition_str__returns_readable_representation_of_condition(
    segment: Segment,
    segment_rule: SegmentRule,
) -> None:
    # Given
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
    )

    # When
    result = str(condition)

    # Then
    assert result == "Condition for ALL rule for Segment - segment: foo EQUAL bar"


def test_Condition_get_skip_create_audit_log__returns_true(
    segment_rule: SegmentRule,
) -> None:
    # Given
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
    )

    # When
    result = condition.get_skip_create_audit_log()

    # Then
    assert result is True


def test_manager_returns_only_highest_version_of_segments(
    segment: Segment,
) -> None:
    # Given
    cloned_segment = segment.clone(is_revision=True)

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
    "get_parents",
    [
        lambda segment, rule: {"segment": segment, "rule": rule},
        lambda segment, rule: {"segment": None, "rule": None},
    ],
)
def test_SegmentRule_clean__validates_rule_has_only_one_parent(
    get_parents: Callable[[Segment, SegmentRule], dict[str, Any]],
    segment: Segment,
    segment_rule: SegmentRule,
) -> None:
    # Given
    parents = get_parents(segment, segment_rule)
    rule = SegmentRule(**parents)

    # When
    with pytest.raises(ValidationError) as exc_info:
        rule.clean()

    # Then
    parents_count = sum(parent is not None for parent in parents.values())
    assert exc_info.match(
        f"SegmentRule must have exactly one parent, {parents_count} found"
    )


def test_SegmentRule_get_skip_create_audit_log__returns_true(
    segment: Segment,
) -> None:
    # Given
    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
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


def test_system_segment_get_skip_create_audit_log(system_segment: Segment) -> None:
    # When
    result = system_segment.get_skip_create_audit_log()

    # Then
    assert result is True


def test_system_segment_rule_get_skip_create_audit_log(system_segment: Segment) -> None:
    # Given
    segment_rule = SegmentRule.objects.create(
        segment=system_segment,
        type=SegmentRule.ALL_RULE,
    )

    # When
    result = segment_rule.get_skip_create_audit_log()

    # Then
    assert result is True


def test_system_segment_condition_get_skip_create_audit_log(
    system_segment: Segment,
) -> None:
    # Given
    segment_rule = SegmentRule.objects.create(
        segment=system_segment,
        type=SegmentRule.ALL_RULE,
    )
    condition = Condition.objects.create(
        rule=segment_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
    )
    # When
    result = condition.get_skip_create_audit_log()
    # Then
    assert result is True

    
def test_Segment_clone__can_create_standalone_segment_clone(
    segment: Segment,
) -> None:
    # Given
    segment.version = 5
    segment.save()

    # When
    cloned_segment = segment.clone(name="another-segment", is_revision=False)

    # Then
    assert cloned_segment != segment
    assert cloned_segment.name == "another-segment"
    assert cloned_segment.version_of == cloned_segment
    assert cloned_segment.version == 1


def test_Segment_clone__empty_segment__returns_new_revision(
    segment: Segment,
) -> None:
    # Given
    original_version: int = segment.version  # type: ignore[assignment]

    # When
    cloned_segment = segment.clone(is_revision=True)

    # Then
    assert cloned_segment != segment
    assert cloned_segment.version_of == segment
    assert cloned_segment.version == original_version
    assert segment.version == original_version + 1


@pytest.mark.parametrize("is_revision", [True, False])
def test_Segment_clone__segment_with_rules__returns_new_segment_with_copied_rules_and_conditions(
    is_revision: bool,
    segment: Segment,
) -> None:
    # Given
    rule1 = SegmentRule.objects.create(
        segment=segment,
        type=SegmentRule.ALL_RULE,
    )
    Condition.objects.create(
        rule=rule1,
        property="property1a",
        operator=EQUAL,
        value="value1a",
    )
    Condition.objects.create(
        rule=rule1,
        property="property1b",
        operator=EQUAL,
        value="value1b",
    )
    rule2 = SegmentRule.objects.create(
        segment=segment,
        type=SegmentRule.ANY_RULE,
    )
    Condition.objects.create(
        rule=rule2,
        property="property2a",
        operator=EQUAL,
        value="value2a",
    )
    rule3 = SegmentRule.objects.create(
        rule=rule2,
        type=SegmentRule.ALL_RULE,
    )
    Condition.objects.create(
        rule=rule3,
        property="property3a",
        operator=EQUAL,
        value="value3a",
    )

    # When
    cloned_segment = segment.clone(is_revision=is_revision)

    # Then
    assert cloned_segment != segment
    assert list(
        SegmentRule.objects.filter(segment=cloned_segment)
        .values("rule", "type")
        .order_by("type")
    ) == [
        {"rule": None, "type": SegmentRule.ALL_RULE},
        {"rule": None, "type": SegmentRule.ANY_RULE},
    ]
    assert list(
        Condition.objects.filter(rule__segment=cloned_segment)
        .values("property", "operator", "value")
        .order_by("property")
    ) == [
        {"property": "property1a", "operator": EQUAL, "value": "value1a"},
        {"property": "property1b", "operator": EQUAL, "value": "value1b"},
        {"property": "property2a", "operator": EQUAL, "value": "value2a"},
    ]
    assert list(
        SegmentRule.objects.filter(rule__segment=cloned_segment).values(
            "rule__type", "type"
        )
    ) == [
        {"rule__type": SegmentRule.ANY_RULE, "type": SegmentRule.ALL_RULE},
    ]
    assert list(
        Condition.objects.filter(rule__rule__segment=cloned_segment).values(
            "property", "operator", "value"
        )
    ) == [
        {"property": "property3a", "operator": EQUAL, "value": "value3a"},
    ]

