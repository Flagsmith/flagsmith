from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import Metadata, MetadataField


class MetadataFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataField
        fields = ("id", "name", "type", "description", "is_required", "organisation")


class ContentObjectSerializer(serializers.Serializer):
    content_type = serializers.CharField()
    object_id = serializers.IntegerField()

    def to_representation(self, value):
        content_type = self.parent.instance.content_type
        return {"object_type": content_type.name, "object_id": value.id}

    def to_internal_value(self, data):
        # TODO: restructure to avoid local import
        from .views import metadata_resource_map

        if data["object_type"] not in metadata_resource_map:
            raise serializers.ValidationError("Invalid content type")

        object_type = ContentType.objects.get(
            app_label=metadata_resource_map[data["object_type"]],
            model=data["object_type"],
        )
        return object_type.model_class().objects.get(pk=data["object_id"])


class MetadataSerializer(serializers.ModelSerializer):
    content_object = ContentObjectSerializer()

    class Meta:
        model = Metadata
        fields = ("id", "field", "field_data", "content_object")
        read_only_fields = ("id",)
