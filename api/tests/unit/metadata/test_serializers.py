import pytest

from metadata.models import (
    FIELD_VALUE_MAX_LENGTH,
    MetadataField,
    MetadataModelField,
)
from metadata.serializers import MetadataSerializer


@pytest.mark.parametrize(
    "field_type, field_value, expected_is_valid",
    [
        ("int", "1", True),
        ("int", "string", False),
        ("float", "1.0", True),
        ("float", "string", False),
        ("bool", "True", True),
        ("bool", "true", True),
        ("bool", "False", True),
        ("bool", "false", True),
        ("bool", "10", False),
        ("bool", "string", False),
        ("url", "not a valid url", False),
        ("url", "https://flagsmith.com", True),
        ("string", "a long string" * FIELD_VALUE_MAX_LENGTH, False),
    ],
)
def test_metadata_serializer_validate_validates_field_value_type_correctly(
    organisation, environment_content_type, field_type, field_value, expected_is_valid
):
    # Given
    field = MetadataField.objects.create(
        name="b", type=field_type, organisation=organisation
    )

    model_field = MetadataModelField.objects.create(
        field=field, content_type=environment_content_type
    )

    data = {"model_field": model_field.id, "field_value": field_value}

    serializer = MetadataSerializer(data=data)

    # When/ Then
    assert serializer.is_valid() is expected_is_valid
