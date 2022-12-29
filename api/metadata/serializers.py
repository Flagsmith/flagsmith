from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import serializers

from .models import (
    FIELD_DATA_MAX_LENGTH,
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
        read_only_fields = ("id",)


# class AssignMetadataFieldSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MetadataModelField
#         fields = ("id", "field", "is_required")
#         read_only_fields = ("id",)


# class ContentObjectSerializer(serializers.Serializer):
#     content_type = serializers.CharField()
#     object_id = serializers.IntegerField()

#     def to_representation(self, value):
#         content_type = self.parent.instance.content_type
#         return {"object_type": content_type.name, "object_id": value.id}

#     def to_internal_value(self, data):
#         # TODO: restructure to avoid local import
#         from .views import metadata_resource_map

#         if data["object_type"] not in metadata_resource_map:
#             raise serializers.ValidationError("Invalid content type")

#         object_type = ContentType.objects.get(
#             app_label=metadata_resource_map[data["object_type"]],
#             model=data["object_type"],
#         )
#         return object_type.model_class().objects.get(pk=data["object_id"])


class FieldDataField(serializers.Field):
    """
    Custom field to handle the different types of data supported by the metadata field
    """

    def to_internal_value(self, data):
        data_type = type(data).__name__

        if data_type not in [field.value for field in FieldType.__members__.values()]:
            raise serializers.ValidationError("Invalid data type")

        if data_type == str and len(data) > FIELD_DATA_MAX_LENGTH:
            raise serializers.ValidationError(
                f"Value string is too long. Must be less than {FIELD_DATA_MAX_LENGTH} character"
            )
        return data

    def to_representation(self, value):
        return value


class MetadataListSerializer(serializers.ListSerializer):
    def save(self, **kwargs):
        validated_data = [{**attrs, **kwargs} for attrs in self.validated_data]
        content_type = ContentType.objects.get_for_model(kwargs["content_object"])
        instances = []

        # Create or update the metadata
        for metadata in validated_data:
            instance, _ = Metadata.objects.update_or_create(
                content_type=content_type,
                object_id=metadata["content_object"].id,
                field=metadata["field"],
                defaults={"field_data": metadata["field_data"]},
            )
            instances.append(instance)

        # Delete the metadata that is not in the list
        # TODO: fix this
        Metadata.objects.filter(
            ~Q(id__in=[instance.id for instance in instances]),
            content_type=content_type,
            object_id=metadata["content_object"].id,
            field=metadata["field"],
        ).delete()

        return instances


class MetadataSerializer(serializers.ModelSerializer):
    field_data = FieldDataField()

    class Meta:
        model = Metadata
        fields = ("id", "field", "field_data")
        read_only_fields = ("id",)
        list_serializer_class = MetadataListSerializer

    def validate(self, data):
        if type(data["field_data"]).__name__ != data["field"].field.type:
            raise serializers.ValidationError("Invalid type")
        return data

    def save(self, **kwargs):
        return super().save(**kwargs)


class MetadataSerializerMixin:
    def check_required_metadata(self, metadata_fields: list):
        app_label = self.context["view"].app_label
        model_name = self.context["view"].model_name

        content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        required_metadata_fields = MetadataModelField.objects.filter(
            content_type=content_type, is_required=True
        )

        for metadata_field in required_metadata_fields:
            if not any([field["field"] == metadata_field for field in metadata_fields]):
                raise serializers.ValidationError(
                    f"Missing required metadata field {metadata_field.field.name}"
                )
