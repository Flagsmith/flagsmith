from rest_framework import serializers

from audit.models import ENVIRONMENT_CREATED_MESSAGE, ENVIRONMENT_UPDATED_MESSAGE, RelatedObjectType, AuditLog
from environments.models import Environment, Webhook
from features.serializers import FeatureStateSerializerFull
from projects.serializers import ProjectSerializer


class EnvironmentSerializerFull(serializers.ModelSerializer):
    feature_states = FeatureStateSerializerFull(many=True)
    project = ProjectSerializer()

    class Meta:
        model = Environment
        fields = ('id', 'name', 'feature_states', 'project', 'api_key', 'amplitude_api_key')


class EnvironmentSerializerLight(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = ('id', 'name', 'api_key', 'project', 'amplitude_api_key')
        read_only_fields = ('api_key',)

    def create(self, validated_data):
        instance = super(EnvironmentSerializerLight, self).create(validated_data)
        self._create_audit_log(instance, True)
        return instance

    def update(self, instance, validated_data):
        updated_instance = super(EnvironmentSerializerLight, self).update(instance, validated_data)
        self._create_audit_log(instance, False)
        return updated_instance

    def _create_audit_log(self, instance, created):
        message = (ENVIRONMENT_CREATED_MESSAGE if created else ENVIRONMENT_UPDATED_MESSAGE) % instance.name
        request = self.context.get('request')
        AuditLog.objects.create(author=request.user if request else None,
                                related_object_id=instance.id,
                                related_object_type=RelatedObjectType.ENVIRONMENT.name,
                                environment=instance,
                                project=instance.project,
                                log=message)


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ('id', 'url', 'enabled', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


