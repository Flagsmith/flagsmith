from rest_framework import serializers

from audit.models import (
    ENVIRONMENT_CREATED_MESSAGE,
    ENVIRONMENT_UPDATED_MESSAGE,
    AuditLog,
    RelatedObjectType,
)
from environments.models import Environment, EnvironmentAPIKey, Webhook
from features.serializers import FeatureStateSerializerFull
from projects.serializers import ProjectSerializer


class EnvironmentSerializerFull(serializers.ModelSerializer):
    feature_states = FeatureStateSerializerFull(many=True)
    project = ProjectSerializer()

    class Meta:
        model = Environment
        fields = (
            "id",
            "name",
            "feature_states",
            "project",
            "api_key",
        )


class EnvironmentSerializerLight(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = (
            "id",
            "name",
            "api_key",
            "project",
        )

    def create(self, validated_data):
        instance = super(EnvironmentSerializerLight, self).create(validated_data)
        self._create_audit_log(instance, True)
        return instance

    def update(self, instance, validated_data):
        updated_instance = super(EnvironmentSerializerLight, self).update(
            instance, validated_data
        )
        self._create_audit_log(instance, False)
        return updated_instance

    def _create_audit_log(self, instance, created):
        message = (
            ENVIRONMENT_CREATED_MESSAGE if created else ENVIRONMENT_UPDATED_MESSAGE
        ) % instance.name
        request = self.context.get("request")
        AuditLog.objects.create(
            author=getattr(request, "user", None),
            related_object_id=instance.id,
            related_object_type=RelatedObjectType.ENVIRONMENT.name,
            environment=instance,
            project=instance.project,
            log=message,
        )


class CloneEnvironmentSerializer(EnvironmentSerializerLight):
    class Meta:
        model = Environment
        fields = ("id", "name", "api_key", "project")
        read_only_fields = ("id", "api_key", "project")

    def create(self, validated_data):
        name = validated_data.get("name")
        source_env = validated_data.get("source_env")
        clone = source_env.clone(name)
        self._create_audit_log(clone, True)
        return clone


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ("id", "url", "enabled", "created_at", "updated_at", "secret")
        read_only_fields = ("id", "created_at", "updated_at")


class EnvironmentAPIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvironmentAPIKey
        fields = ("id", "key", "active", "created_at", "name", "expires_at")
        read_only_fields = ("id", "created_at")
