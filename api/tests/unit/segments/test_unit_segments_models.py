from segments.models import PERCENTAGE_SPLIT, Condition


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
