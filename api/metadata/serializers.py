from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import serializers

from .models import (
    FIELD_VALUE_MAX_LENGTH,
    FieldType,
    Metadata,
    MetadataField,
    MetadataModelField,
)


class MetadataFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataField
        fields = ("id", "name", "type", "description", "organisation")


class MetaDataModelFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataModelField
        fields = ("id", "field", "is_required")


class FieldDataField(serializers.Field):
    """
    Custom field to handle the different types of data supported by the metadata field
    """

    def to_internal_value(self, data):
        data_type = type(data).__name__

        if data_type not in [field.value for field in FieldType.__members__.values()]:
            raise serializers.ValidationError("Invalid data type")

        if data_type == str and len(data) > FIELD_VALUE_MAX_LENGTH:
            raise serializers.ValidationError(
                f"Value string is too long. Must be less than {FIELD_VALUE_MAX_LENGTH} character"
            )
        return data

    def to_representation(self, value):
        return value


class MetadataListSerializer(serializers.ListSerializer):
    def save(self, **kwargs):
        validated_data = [{**attrs, **kwargs} for attrs in self.validated_data]
        content_object = kwargs["content_object"]
        content_type = ContentType.objects.get_for_model(content_object)
        instances = []

        # Create or update the metadata
        for metadata in validated_data:
            instance, _ = Metadata.objects.update_or_create(
                content_type=content_type,
                object_id=content_object.id,
                model_field=metadata["model_field"],
                defaults={"field_value": metadata["field_value"]},
            )
            instances.append(instance)

        # Delete the metadata not in the list
        Metadata.objects.filter(
            ~Q(id__in=[instance.id for instance in instances]),
            content_type=content_type,
            object_id=content_object.id,
        ).delete()

        return instances


class MetadataSerializer(serializers.ModelSerializer):
    field_value = FieldDataField()

    class Meta:
        model = Metadata
        fields = ("model_field", "field_value")
        list_serializer_class = MetadataListSerializer

    def validate(self, data):
        if type(data["field_value"]).__name__ != data["model_field"].field.type:
            raise serializers.ValidationError("Invalid type")
        return data

    def to_representation(self, value):
        # Convert field_value to its appropriate type(from string)
        field_type = value.model_field.field.type
        value = super().to_representation(value)

        value["field_value"] = {
            "str": str,
            "int": int,
            "float": float,
            "bool": lambda v: v not in ("False", "false"),
        }.get(field_type)(value["field_value"])

        return value


class MetadataSerializerMixin:
    def validate_required_metadata(self):
        metadata = self.validated_data.pop("metadata", [])

        content_type = ContentType.objects.get_for_model(self.Meta.model)

        required_metadata_fields = MetadataModelField.objects.filter(
            content_type=content_type, is_required=True
        )

        for metadata_field in required_metadata_fields:
            if not any([field["model_field"] == metadata_field for field in metadata]):
                raise serializers.ValidationError(
                    f"Missing required metadata field {metadata_field.field.name}"
                )

    def save(self, **kwargs):
        self.validate_required_metadata()

        instance = super().save(**kwargs)

        metadata = self.get_initial().get("metadata", None)

        if metadata:
            metadata_serializer = MetadataSerializer(
                data=metadata, many=True, context=self.context
            )

            metadata_serializer.is_valid(raise_exception=True)
            metadata_serializer.save(content_object=instance)

        return instance
