from rest_framework import serializers

from integrations.launch_darkly.models import LaunchDarklyImportRequest


class LaunchDarklyImportRequestStatusSerializer(serializers.Serializer):  # type: ignore[type-arg]
    requested_environment_count = serializers.IntegerField(read_only=True)
    requested_flag_count = serializers.IntegerField(read_only=True)
    result = serializers.ChoiceField(
        ["success", "failure"],
        read_only=True,
        allow_null=True,
    )
    error_messages = serializers.ListSerializer(  # type: ignore[assignment]
        child=serializers.CharField(read_only=True)
    )


class CreateLaunchDarklyImportRequestSerializer(serializers.Serializer):  # type: ignore[type-arg]
    token = serializers.CharField()
    project_key = serializers.CharField()


class LaunchDarklyImportRequestSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    created_by = serializers.SlugRelatedField(slug_field="email", read_only=True)  # type: ignore[var-annotated]
    status = LaunchDarklyImportRequestStatusSerializer()

    class Meta:
        model = LaunchDarklyImportRequest
        fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "completed_at",
            "status",
            "project",
        )
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "completed_at",
            "status",
            "project",
        )
