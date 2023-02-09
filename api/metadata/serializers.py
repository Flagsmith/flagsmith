from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from organisations.models import Organisation
from projects.models import Project
from util.drf_writable_nested.serializers import (
    DeleteBeforeUpdateWritableNestedModelSerializer,
)

from .models import (
    Metadata,
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)


class MetadataFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataField
        fields = ("id", "name", "type", "description", "organisation")


class MetadataModelFieldRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataModelFieldRequirement
        fields = ("content_type", "object_id")


class MetaDataModelFieldSerializer(DeleteBeforeUpdateWritableNestedModelSerializer):
    is_required_for = MetadataModelFieldRequirementSerializer(many=True, required=False)

    class Meta:
        model = MetadataModelField
        fields = ("id", "field", "content_type", "is_required_for")


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ("id", "app_label", "model")


class MetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metadata
        fields = ("id", "model_field", "field_value")

    def validate(self, data):
        data = super().validate(data)
        if not data["model_field"].field.is_field_value_valid(data["field_value"]):
            raise serializers.ValidationError(
                f"Invalid value for field {data['model_field'].field.name}"
            )

        return data


class MetadataSerializerMixin:
    def get_organisation_from_validated_data(self, validated_data) -> Organisation:
        raise NotImplementedError()

    def get_project_from_validated_data(self, validated_data) -> Project:
        raise NotImplementedError()

    def get_fetch_method(self, model_name):
        return {
            "project": self.get_project_from_validated_data,
            "organisation": self.get_organisation_from_validated_data,
        }[model_name]

    def validate_required_metadata(self, data):
        metadata = data.get("metadata", [])

        content_type = ContentType.objects.get_for_model(self.Meta.model)

        organisation = self.get_organisation_from_validated_data(data)
        required_for_qs = MetadataModelFieldRequirement.objects.filter(
            model_field__content_type=content_type,
            model_field__field__organisation=organisation,
        )
        for required_for in required_for_qs:
            model_name = required_for.content_type.model
            object = self.get_fetch_method(model_name)(data)
            if object.id == required_for.object_id:
                if not any(
                    [
                        field["model_field"] == required_for.model_field
                        for field in metadata
                    ]
                ):
                    raise serializers.ValidationError(
                        {
                            "metadata": f"Missing required metadata field: {required_for.model_field.field.name}"
                        }
                    )

    def validate(self, data):
        data = super().validate(data)
        self.validate_required_metadata(data)
        return data
