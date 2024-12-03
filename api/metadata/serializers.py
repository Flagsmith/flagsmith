from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from util.drf_writable_nested.serializers import (
    DeleteBeforeUpdateWritableNestedModelSerializer,
)

from .models import (
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)


class MetadataFieldQuerySerializer(serializers.Serializer):
    organisation = serializers.IntegerField(
        required=True, help_text="Organisation ID to filter by"
    )


class SupportedRequiredForModelQuerySerializer(serializers.Serializer):
    model_name = serializers.CharField(required=True)


class MetadataFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataField
        fields = ("id", "name", "type", "description", "organisation")


class MetadataModelFieldQuerySerializer(serializers.Serializer):
    content_type = serializers.IntegerField(
        required=False, help_text="Content type of the model to filter by."
    )


class MetadataModelFieldRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataModelFieldRequirement
        fields = ("content_type", "object_id")


class MetaDataModelFieldSerializer(DeleteBeforeUpdateWritableNestedModelSerializer):
    is_required_for = MetadataModelFieldRequirementSerializer(many=True, required=False)

    class Meta:
        model = MetadataModelField
        fields = ("id", "field", "content_type", "is_required_for")

    def validate(self, data):
        data = super().validate(data)
        for requirement in data.get("is_required_for", []):
            org_id = (
                requirement["content_type"]
                .model_class()
                .objects.get(id=requirement["object_id"])
                .organisation_id
            )
            if org_id != data["field"].organisation_id:
                raise serializers.ValidationError(
                    "The requirement organisation does not match the field organisation"
                )
        return data


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ("id", "app_label", "model")
