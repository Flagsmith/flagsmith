from rest_framework import serializers

from features.serializers import FeatureStateSerializerFull
from environments.models import Environment, Identity
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
        fields = ('id', 'name', 'api_key', 'project')
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
