from rest_framework import serializers, exceptions

from features.serializers import FeatureStateSerializerFull
from environments.models import Environment, Identity, Trait, INTEGER
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
        query_data, defaults = self._build_trait_data(validated_data)
        trait, _ = Trait.objects.get_or_create(**query_data, defaults=defaults)

        if trait.value_type != INTEGER:
            raise exceptions.ValidationError('Trait is not an integer.')

        trait.integer_value += validated_data.get('increment_by')
        trait.save()
        return trait

    def _build_trait_data(self, validated_data):
        return self._build_query_data(validated_data), self._build_default_data()

    def _build_query_data(self, validated_data):
        identity, _ = Identity.objects.get_or_create(identifier=validated_data.get('identifier'),
                                                     environment=self.context.get('request').environment)

        return {
            'trait_key': validated_data.get('trait_key'),
            'identity': identity
        }

    def _build_default_data(self):
        return {
            'value_type': INTEGER,
            'integer_value': 0
        }

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
