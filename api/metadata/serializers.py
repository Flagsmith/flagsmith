from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Model
from rest_framework import serializers

from metadata.models import (
    Metadata,
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)
from organisations.models import Organisation
from util.drf_writable_nested.serializers import (
    DeleteBeforeUpdateWritableNestedModelSerializer,
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
            elif model_type == "project":
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
            else:
                raise serializers.ValidationError(
                    "The requirement content type must be project or organisation"
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


class MetadataSerializer(serializers.ModelSerializer[Metadata]):
    class Meta:
        model = Metadata
        fields = ("id", "model_field", "field_value")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs = super().validate(attrs)
        model_field = attrs["model_field"].field
        if not model_field.is_field_value_valid(attrs["field_value"]):
            raise serializers.ValidationError(
                f"Invalid value for field {model_field.name}"
            )
        return attrs


class MetadataSerializerMixin(serializers.Serializer):  # type: ignore[type-arg]
    """
    Mixin for serializers that need to handle metadata

    NOTE: Child serializers should include 'metadata' in their Meta.fields.
    """

    metadata = MetadataSerializer(required=False, many=True)

    def _validate_required_metadata(
        self, organisation: Organisation, metadata: list[dict[str, Any]]
    ) -> None:
        content_type = ContentType.objects.get_for_model(self.Meta.model)  # type: ignore[attr-defined]
        requirements = MetadataModelFieldRequirement.objects.filter(
            model_field__content_type=content_type,
            model_field__field__organisation=organisation,
        ).select_related("model_field__field")

        metadata_fields = {field["model_field"] for field in metadata}
        for requirement in requirements:
            if requirement.model_field not in metadata_fields:
                field_name = requirement.model_field.field.name
                raise serializers.ValidationError(
                    {"metadata": f"Missing required metadata field: {field_name}"}
                )

    def _update_metadata(
        self,
        instance: Model,
        metadata_data: list[dict[str, Any]],
    ) -> None:
        content_type = ContentType.objects.get_for_model(type(instance))
        existing_metadata = Metadata.objects.filter(
            object_id=instance.pk,
            content_type=content_type,
        )

        new_metadata = [
            Metadata(
                model_field=model_field,
                content_type=content_type,
                object_id=instance.pk,
                field_value=metadata_item["field_value"],
            )
            for metadata_item in metadata_data
            if (model_field := metadata_item["model_field"]) and model_field.pk
        ]

        with transaction.atomic():
            existing_metadata.delete()
            Metadata.objects.bulk_create(new_metadata)
