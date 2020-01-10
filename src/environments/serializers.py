from rest_framework import serializers, exceptions

from audit.models import ENVIRONMENT_CREATED_MESSAGE, ENVIRONMENT_UPDATED_MESSAGE, RelatedObjectType, AuditLog
from environments.models import Environment, Identity, Trait, INTEGER, Webhook
from features.serializers import FeatureStateSerializerFull
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
        fields = ('id', 'name', 'api_key', 'project')
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
        fields = ('id', 'trait_key', 'trait_value')

    @staticmethod
    def get_trait_value(obj):
        return obj.get_trait_value()


class IncrementTraitValueSerializer(serializers.Serializer):
    trait_key = serializers.CharField()
    increment_by = serializers.IntegerField(write_only=True)
    identifier = serializers.CharField()
    trait_value = serializers.IntegerField(read_only=True)

    def to_representation(self, instance):
        return {
            'trait_key': instance.trait_key,
            'trait_value': instance.integer_value,
            'identifier': instance.identity.identifier
        }

    def create(self, validated_data):
        trait, _ = Trait.objects.get_or_create(**self._build_query_data(validated_data),
                                               defaults=self._build_default_data())

        if trait.value_type != INTEGER:
            raise exceptions.ValidationError('Trait is not an integer.')

        trait.integer_value += validated_data.get('increment_by')
        trait.save()
        return trait

    def _build_query_data(self, validated_data):
        identity_data = {
            'identifier': validated_data.get('identifier'),
            'environment': self.context.get('request').environment
        }
        identity, _ = Identity.objects.get_or_create(**identity_data)

        return {
            'trait_key': validated_data.get('trait_key'),
            'identity': identity
        }

    def _build_default_data(self):
        return {
            'value_type': INTEGER,
            'integer_value': 0
        }


class TraitKeysSerializer(serializers.Serializer):
    keys = serializers.ListSerializer(child=serializers.CharField())


class DeleteAllTraitKeysSerializer(serializers.Serializer):
    key = serializers.CharField()

    def delete(self):
        environment = self.context.get('environment')
        Trait.objects.filter(identity__environment=environment, trait_key=self.validated_data.get('key')).delete()


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


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ('id', 'url', 'enabled', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
