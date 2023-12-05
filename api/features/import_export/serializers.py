from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .constants import MAX_FEATURE_IMPORT_SIZE, OVERWRITE_DESTRUCTIVE, SKIP
from .models import FeatureExport, FeatureImport
from .tasks import export_features_for_environment


class CreateFeatureExportSerializer(serializers.Serializer):
    environment_id = serializers.IntegerField(required=True)
    tag_ids = serializers.ListField(child=serializers.IntegerField())

    def save(self) -> None:
        export_features_for_environment.delay(
            kwargs={
                "environment_id": self.validated_data["environment_id"],
                "tag_ids": self.validated_data["tag_ids"],
            }
        )


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


def validate_feature_import_file_size(upload_file: InMemoryUploadedFile) -> None:
    if upload_file.size > MAX_FEATURE_IMPORT_SIZE:
        raise ValidationError("File size is too large.")


class FeatureImportUploadSerializer(serializers.Serializer):
    file = serializers.FileField(
        validators=[validate_feature_import_file_size],
    )
    strategy = serializers.ChoiceField(choices=[SKIP, OVERWRITE_DESTRUCTIVE])


class FeatureImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureImport
        fields = (
            "id",
            "environment_id",
            "status",
            "created_at",
        )
