from rest_framework import serializers

from .models import Feature, FeatureState, FeatureStateValue


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = "__all__"


class FeatureStateSerializerFull(serializers.ModelSerializer):
    feature = FeatureSerializer()
    feature_state_value = serializers.SerializerMethodField()

    class Meta:
        model = FeatureState
        fields = "__all__"

    def get_feature_state_value(self, obj):
        return obj.get_feature_state_value()


class FeatureStateSerializerBasic(serializers.ModelSerializer):
    feature_state_value = serializers.SerializerMethodField()

    class Meta:
        model = FeatureState
        fields = "__all__"

    def get_feature_state_value(self, obj):
        return obj.get_feature_state_value()


class FeatureStateSerializerCreate(serializers.ModelSerializer):

    class Meta:
        model = FeatureState
        fields = ('feature', 'enabled')


class FeatureStateValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureStateValue
        fields = "__all__"
