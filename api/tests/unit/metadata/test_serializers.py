import pytest
from common.metadata.serializers import MetadataSerializer  # type: ignore[import-untyped]

from metadata.models import (
    FIELD_VALUE_MAX_LENGTH,
    MetadataField,
    MetadataModelField,
)


@pytest.mark.parametrize(
    "field_type, field_value, expected_is_valid",
    [
        ("int", "1", True),
        ("int", "string", False),
        ("bool", "True", True),
        ("bool", "true", True),
        ("bool", "False", True),
        ("bool", "false", True),
        ("bool", "10", False),
        ("bool", "string", False),
        ("url", "not a valid url", False),
        ("url", "https://flagsmith.com", True),
        ("str", "a long string" * FIELD_VALUE_MAX_LENGTH, False),
        ("str", "a valid string", True),
        ("multiline_str", "a valid string", True),
    ],
)
def test_metadata_serializer_validate_validates_field_value_type_correctly(  # type: ignore[no-untyped-def]
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
