from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .constants import (
    MAX_FEATURE_IMPORT_SIZE,
    OVERWRITE_DESTRUCTIVE,
    PROCESSING,
    SKIP,
)
from .models import FeatureExport, FeatureImport
from .tasks import (
    export_features_for_environment,
    import_features_for_environment,
)


class CreateFeatureExportSerializer(serializers.Serializer):
    environment_id = serializers.IntegerField(required=True)
    tag_ids = serializers.ListField(child=serializers.IntegerField())

    def save(self) -> FeatureExport:
        feature_export = FeatureExport.objects.create(
            environment_id=self.validated_data["environment_id"],
            status=PROCESSING,
        )

        export_features_for_environment.delay(
            kwargs={
                "feature_export_id": feature_export.id,
                "tag_ids": self.validated_data["tag_ids"],
            }
        )

        return feature_export


class FeatureExportSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = FeatureExport
        fields = (
            "id",
            "name",
            "environment_id",
            "status",
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

    def save(self, environment_id: int) -> FeatureImport:
        if FeatureImport.objects.filter(
            environment_id=environment_id,
            status=PROCESSING,
        ).exists():
            raise ValidationError(
                "Can't import features, since already processing a feature import."
            )

        uploaded_file = self.validated_data["file"]
        strategy = self.validated_data["strategy"]
        file_content = uploaded_file.read().decode("utf-8")
        feature_import = FeatureImport.objects.create(
            environment_id=environment_id,
            strategy=strategy,
            data=file_content,
        )
        import_features_for_environment.delay(
            kwargs={"feature_import_id": feature_import.id}
        )
        return feature_import


class FeatureImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureImport
        fields = (
            "id",
            "environment_id",
            "strategy",
            "status",
            "created_at",
        )
