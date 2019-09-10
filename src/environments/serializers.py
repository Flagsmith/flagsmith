from rest_framework import serializers

from audit.models import ENVIRONMENT_CREATED_MESSAGE, ENVIRONMENT_UPDATED_MESSAGE, RelatedObjectType, AuditLog
from features.serializers import FeatureStateSerializerFull
from environments.models import Environment, Identity, Trait
from projects.serializers import ProjectSerializer
from segments.serializers import SegmentSerializerBasic


class EnvironmentSerializerFull(serializers.ModelSerializer):
    feature_states = FeatureStateSerializerFull(many=True)
    project = ProjectSerializer()

    class Meta:
        model = Environment
        fields = ('id', 'name', 'feature_states', 'project', 'api_key')


class EnvironmentSerializerLight(serializers.ModelSerializer):

    class Meta:
        model = Environment
        fields = ('id', 'name', 'api_key', 'project', 'webhooks_enabled', 'webhook_url')
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
        message = ENVIRONMENT_CREATED_MESSAGE if created else ENVIRONMENT_UPDATED_MESSAGE % instance.name
        request = self.context.get('request')
        AuditLog.objects.create(author=request.user if request else None,
                                related_object_id=instance.id,
                                related_object_type=RelatedObjectType.ENVIRONMENT.name,
                                environment=instance,
                                log=message)


class IdentitySerializerFull(serializers.ModelSerializer):
    identity_features = FeatureStateSerializerFull(many=True)
    environment = EnvironmentSerializerFull()

    class Meta:
        model = Identity
        fields = ('id', 'identifier', 'identity_features', 'environment')


class IdentitySerializer(serializers.ModelSerializer):

    class Meta:
        model = Identity
        fields = ('id', 'identifier', 'environment')


class TraitSerializerFull(serializers.ModelSerializer):
    identity = IdentitySerializer()
    trait_value = serializers.SerializerMethodField()

    class Meta:
        model = Trait
        fields = "__all__"

    @staticmethod
    def get_trait_value(obj):
        return obj.get_trait_value()


class TraitSerializerBasic(serializers.ModelSerializer):
    trait_value = serializers.SerializerMethodField()

    class Meta:
        model = Trait
        fields = ('trait_key', 'trait_value')

    @staticmethod
    def get_trait_value(obj):
        return obj.get_trait_value()


# Serializer for returning both Feature Flags and User Traits
class IdentitySerializerTraitFlags(serializers.Serializer):
    flags = FeatureStateSerializerFull(many=True)
    traits = TraitSerializerBasic(many=True)


class IdentitySerializerWithTraitsAndSegments(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    flags = FeatureStateSerializerFull(many=True)
    traits = TraitSerializerBasic(many=True)
    segments = SegmentSerializerBasic(many=True)
