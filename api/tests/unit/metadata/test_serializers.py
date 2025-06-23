from typing import Any, Callable, Dict

import pytest
from common.metadata.serializers import (
    MetadataSerializer,
)
from django.contrib.contenttypes.models import ContentType

from metadata.models import (
    FIELD_VALUE_MAX_LENGTH,
    MetadataField,
    MetadataModelField,
)
from metadata.serializers import MetaDataModelFieldSerializer
from organisations.models import Organisation
from projects.models import Project


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
def test_metadata_serializer_validate_validates_field_value_type_correctly(
    organisation: Organisation,
    environment_content_type: ContentType,
    field_type: str,
    field_value: str,
    expected_is_valid: bool,
) -> None:
    # Given
    field = MetadataField.objects.create(
        name="b", type=field_type, organisation=organisation
    )

    model_field = MetadataModelField.objects.create(
        field=field, content_type=environment_content_type
    )

    data: Dict[str, Any] = {"model_field": model_field.id, "field_value": field_value}

    serializer = MetadataSerializer(data=data)

    # When/ Then
    assert serializer.is_valid() is expected_is_valid


@pytest.mark.parametrize(
    "content_type_target,expected_is_valid,error_message,get_object_id",
    [
        (
            "organisation",
            True,
            None,
            lambda **kwargs: kwargs["metadata_field"].organisation.id,
        ),
        ("project", True, None, lambda **kwargs: kwargs["project"].id),
        (
            "project",
            False,
            "The requirement organisation does not match the field organisation",
            lambda **kwargs: 9999,
        ),
        (
            "organisation",
            False,
            "The requirement organisation does not match the field organisation",
            lambda **kwargs: 9999,
        ),
    ],
)
def test_metadata_model_field_serializer_validation(
    a_metadata_field: MetadataField,
    feature_content_type: ContentType,
    project: Project,
    content_type_target: str,
    organisation_content_type: ContentType,
    project_content_type: ContentType,
    expected_is_valid: bool,
    error_message: str | None,
    get_object_id: Callable[..., int],
) -> None:
    content_type = (
        organisation_content_type
        if content_type_target == "organisation"
        else project_content_type
    )
    object_id = get_object_id(project=project, metadata_field=a_metadata_field)
    print(f"Metadata field org_id: {a_metadata_field.organisation.id}")
    # Given
    data: Dict[str, Any] = {
        "field": a_metadata_field.id,
        "content_type": feature_content_type.id,
        "is_required_for": [
            {
                "content_type": content_type.id,
                "object_id": object_id,
            }
        ],
    }

    # When
    serializer = MetaDataModelFieldSerializer(data=data)
    result = serializer.is_valid()

    # Then
    assert result is expected_is_valid
    if not expected_is_valid:
        assert "non_field_errors" in serializer.errors
        assert serializer.errors["non_field_errors"][0] == error_message


def test_metadata_model_field_serializer_with_empty_is_required_for(
    a_metadata_field: MetadataField,
    feature_content_type: ContentType,
) -> None:
    # Given
    data: Dict[str, Any] = {
        "field": a_metadata_field.id,
        "content_type": feature_content_type.id,
        "is_required_for": [],
    }
    # When
    serializer = MetaDataModelFieldSerializer(data=data)
    result: bool = serializer.is_valid()
    # Then
    assert result is True


def test_metadata_model_field_serializer_validation_invalid_content_type(
    a_metadata_field: MetadataField,
    feature_content_type: ContentType,
    project: Project,
    segment_content_type: ContentType,
) -> None:
    object_id = project.id

    # Given
    data: Dict[str, Any] = {
        "field": a_metadata_field.id,
        "content_type": feature_content_type.id,
        "is_required_for": [
            {
                "content_type": segment_content_type.id,
                "object_id": object_id,
            }
        ],
    }

    # When
    serializer = MetaDataModelFieldSerializer(data=data)
    result = serializer.is_valid()

    # Then
    assert result is False
    assert "non_field_errors" in serializer.errors
    assert (
        serializer.errors["non_field_errors"][0]
        == "The requirement content type must be project or organisation"
    )
