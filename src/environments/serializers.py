from rest_framework import serializers

from features.serializers import FeatureStateSerializerFull
from environments.models import Environment, Identity, Trait
from projects.serializers import ProjectSerializer


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

    def get_trait_value(self, obj):
        return obj.get_trait_value()


class TraitSerializerBasic(serializers.ModelSerializer):
    trait_value = serializers.SerializerMethodField()

    class Meta:
        model = Trait
        fields = ('trait_key', 'trait_value')

    def get_trait_value(self, obj):
        return obj.get_trait_value()


# Serializer for returning both Feature Flags and User Traits
class IdentitySerializerTraitFlags(serializers.Serializer):
    flags = FeatureStateSerializerFull(many=True)
    traits = TraitSerializerBasic(many=True)
