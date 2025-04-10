from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from typing import Any
from util.drf_writable_nested.serializers import (
    DeleteBeforeUpdateWritableNestedModelSerializer,
)

from .models import (
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)


class MetadataFieldQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    organisation = serializers.IntegerField(
        required=True, help_text="Organisation ID to filter by"
    )


class SupportedRequiredForModelQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    model_name = serializers.CharField(required=True)


class MetadataFieldSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = MetadataField
        fields = ("id", "name", "type", "description", "organisation")


class MetadataModelFieldQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    content_type = serializers.IntegerField(
        required=False, help_text="Content type of the model to filter by."
    )


class MetadataModelFieldRequirementSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = MetadataModelFieldRequirement
        fields = ("content_type", "object_id")


class MetaDataModelFieldSerializer(DeleteBeforeUpdateWritableNestedModelSerializer):
    is_required_for = MetadataModelFieldRequirementSerializer(many=True, required=False)

    class Meta:
        model = MetadataModelField
        fields = ("id", "field", "content_type", "is_required_for")

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        data = super().validate(data)
        for requirement in data.get("is_required_for", []):
            model_type = requirement["content_type"].model
            if model_type == "organisation":
                org_id = requirement["object_id"] 
            else:
                try:
                    org_id = (
                        requirement["content_type"]
                        .model_class()
                        .objects.get(id=requirement["object_id"])
                        .organisation_id
                    )
                except ObjectDoesNotExist:
                    raise serializers.ValidationError(
                        "The requirement organisation does not match the field organisation"
                    )
            if org_id != data["field"].organisation_id:
                raise serializers.ValidationError(
                    "The requirement organisation does not match the field organisation"
                )
        return data


class ContentTypeSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = ContentType
        fields = ("id", "app_label", "model")
