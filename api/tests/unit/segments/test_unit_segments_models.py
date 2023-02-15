import pytest

from segments.models import (
    EQUAL,
    PERCENTAGE_SPLIT,
    Condition,
    Segment,
    SegmentRule,
)


def test_percentage_split_calculation_divides_value_by_100_before_comparison(
    mocker, segment, segment_rule, identity
):
    # Given
    mock_get_hashed_percentage_for_object_ids = mocker.patch(
        "segments.models.get_hashed_percentage_for_object_ids"
    )

    condition = Condition.objects.create(
        rule=segment_rule, operator=PERCENTAGE_SPLIT, value=10
    )
    mock_get_hashed_percentage_for_object_ids.return_value = 0.2

    # When
    result = condition.does_identity_match(identity)

    # Then
    assert not result


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
