from segments.serializers import CloneSegmentSerializer


def test_clone_segment_serializer_validation_without_name_should_fail() -> None:
    # Given
    serializer = CloneSegmentSerializer(data={"name": ""})
    # When
    is_valid = serializer.is_valid()
    errors = serializer.errors
    # Then
    assert not is_valid
    assert errors == {"name": ["This field may not be blank."]}
