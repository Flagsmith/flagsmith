import pytest
from rest_framework import serializers

from metadata.serializers import MetadataSerializer


def test_metadata_serializer_is_valid_raises_error_for_invalid_type(
    a_metadata_field, required_a_environment_metadata_field
):
    # Given - `a_metadata_field` of type integer
    # and
    data = {
        "model_field": required_a_environment_metadata_field.id,
        "field_value": "string",
    }

    serializer = MetadataSerializer(data=data)

    # When
    with pytest.raises(serializers.ValidationError) as e:
        serializer.is_valid(raise_exception=True)

    # Then - correct execption was raised
    "Invalid Type" in str(e.value)


def test_metadata_serializer_converts_field_value_type_correctly(
    a_metadata_field, environment_metadata_a
):
    # Given - `a_metadata_field` of type integer
    # and
    serializer = MetadataSerializer(instance=environment_metadata_a)

    # When
    data = serializer.data

    # Then
    assert isinstance(data["field_value"], int) is True
