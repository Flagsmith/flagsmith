import pytest
from typing import Any, List, Dict, Tuple, Optional, Union, Literal
from common.metadata.serializers import (
    MetadataSerializer,
)

from metadata.models import (
    FIELD_VALUE_MAX_LENGTH,
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement
)

from metadata.serializers import (
    MetaDataModelFieldSerializer
)

from django.contrib.contenttypes.models import ContentType
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
    expected_is_valid: bool
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


def test_metadata_model_field_serializer_validate_requirement_content_type_is_org(
    a_metadata_field: MetadataField, 
    feature_content_type: ContentType, 
    organisation_content_type: ContentType
) -> None:
    # Given
    data: Dict[str, Any] = {
        "field": a_metadata_field.id, 
        "content_type": feature_content_type.id,
        "is_required_for": [
            {
                "content_type": organisation_content_type.id,
                "object_id": a_metadata_field.organisation.id,
            }
        ]
    }
    # When
    serializer = MetaDataModelFieldSerializer(data=data)

    # Then
    assert serializer.is_valid() is True

def test_metadata_model_field_serializer_validate_requirement_content_type_is_project(
    a_metadata_field: MetadataField, 
    feature_content_type: ContentType, 
    project_content_type: ContentType, 
    project: Project
) -> None:
    # Given
    data: Dict[str, Any] = {
        "field": a_metadata_field.id, 
        "content_type": feature_content_type.id,
        "is_required_for": [
            {
                "content_type": project_content_type.id,
                "object_id": project.id,
            }
        ]
    }
    # When
    serializer = MetaDataModelFieldSerializer(data=data)

    # Then
    assert serializer.is_valid() is True

def test_metadata_model_field_serializer_error_with_content_type_project_and_org_id(
    a_metadata_field: MetadataField, 
    feature_content_type: ContentType, 
    project_content_type: ContentType
) -> None:
    # Given
    data: Dict[str, Any] = {
        "field": a_metadata_field.id, 
        "content_type": feature_content_type.id,
        "is_required_for": [
            {
                "content_type": project_content_type.id,
                "object_id": 99999,
            }
        ]
    }
    # When
    serializer = MetaDataModelFieldSerializer(data=data)

    # Then
    assert serializer.is_valid() is False
    assert "non_field_errors" in serializer.errors
    assert serializer.errors["non_field_errors"][0] == "The requirement organisation does not match the field organisation"


def test_metadata_model_field_serializer_error_with_content_type_org_and_wrong_id(
    a_metadata_field: MetadataField, 
    feature_content_type: ContentType, 
    organisation_content_type: ContentType
) -> None:
    # Given
    data: Dict[str, Any] = {
        "field": a_metadata_field.id, 
        "content_type": feature_content_type.id,
        "is_required_for": [
            {
                "content_type": organisation_content_type.id,
                "object_id": 99999,
            }
        ]
    }
    # When
    serializer = MetaDataModelFieldSerializer(data=data)

    # Then
    assert serializer.is_valid() is False
    assert "non_field_errors" in serializer.errors
    assert serializer.errors["non_field_errors"][0] == "The requirement organisation does not match the field organisation"

def test_metadata_serializer_validate_use_org_id_for_content_type_org(
    a_metadata_field: MetadataField,
    feature_content_type: ContentType,
    organisation_content_type: ContentType,
) -> None:
    # Given
    data: Dict[str, Any] = {
        "field": a_metadata_field.id,
        "content_type": feature_content_type.id,
        "is_required_for": [
            {
                "content_type": organisation_content_type.id,
                "object_id": a_metadata_field.organisation.id,
            }
        ]
    }
    serializer = MetaDataModelFieldSerializer(data=data)
    result: bool = serializer.is_valid()
    assert result is True

def test_metadata_serializer_validate_use_project_id_for_content_type_project(
    a_metadata_field: MetadataField,
    feature_content_type: ContentType,
    project_content_type: ContentType,
    project: Project,
) -> None:
    # Given
    data: Dict[str, Any] = {
        "field": a_metadata_field.id,
        "content_type": feature_content_type.id,
        "is_required_for": [
            {
                "content_type": project_content_type.id,
                "object_id": project.id,
            }
        ]
    }
    serializer = MetaDataModelFieldSerializer(data=data)
    result: bool = serializer.is_valid()
    assert result is True

def test_metadata_model_field_serializer_fail_with_content_type_project_and_org_id(
    a_metadata_field: MetadataField,
    feature_content_type: ContentType,
    project_content_type: ContentType,
) -> None:
    # Given
    data: Dict[str, Any] = {
        "field": a_metadata_field.id,
        "content_type": feature_content_type.id,
        "is_required_for": [
            {
                "content_type": project_content_type.id,
                "object_id": 99999,
            }
        ]
    }
    serializer = MetaDataModelFieldSerializer(data=data)
    result: bool = serializer.is_valid()
    assert result is False
    assert "non_field_errors" in serializer.errors
    assert serializer.errors["non_field_errors"][0] == "The requirement organisation does not match the field organisation"
