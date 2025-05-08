import pytest
from rest_framework.exceptions import ErrorDetail, ValidationError

from segments.serializers import CloneSegmentSerializer


def test_clone_segment_serializer_validation_without_name_should_fail() -> None:
    # Given
    serializer = CloneSegmentSerializer()
    # When
    with pytest.raises(ValidationError) as exception:
        serializer.validate({"name": ""})
    # Then
    assert exception.value.detail == [
        ErrorDetail(string="Name is required to clone a segment", code="invalid")
    ]
