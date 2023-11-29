from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .constants import MAX_FEATURE_IMPORT_SIZE
from .models import FeatureExport, FeatureImport


class CreateFeatureExportSerializer(serializers.Serializer):
    environment_id = serializers.IntegerField(required=True)
    tag_ids = serializers.ListField(child=serializers.IntegerField())


class FeatureExportSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = FeatureExport
        fields = (
            "id",
            "name",
            "environment_id",
            "created_at",
        )

    def get_name(self, obj: FeatureExport) -> str:
        return (
            f"{obj.environment.name} | {obj.created_at.strftime('%Y-%m-%d %H:%M')} UTC"
        )


def validate_feature_import_file_size(upload_file):
    if upload_file.size > MAX_FEATURE_IMPORT_SIZE:
        raise ValidationError("File size is too large.")


class FeatureImportUploadSerializer(serializers.Serializer):
    file = serializers.FileField(
        validators=[validate_feature_import_file_size],
    )


class FeatureImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureImport
        fields = (
            "id",
            "environment_id",
            "status",
            "created_at",
        )
