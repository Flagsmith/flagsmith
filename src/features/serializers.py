from rest_framework import serializers

from segments.serializers import SegmentSerializerBasic
from .models import Feature, FeatureState, FeatureStateValue, FeatureSegment


class CreateFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = "__all__"
        read_only_fields = ('feature_segments',)

    def create(self, validated_data):
        if Feature.objects.filter(project=validated_data['project'], name__iexact=validated_data['name']).exists():
            raise serializers.ValidationError("Feature with that name already exists for this "
                                              "project. Note that feature names are case "
                                              "insensitive.")

        super(CreateFeatureSerializer, self).create(validated_data)


class FeatureSegmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureSegment
        fields = ('feature', 'segment', 'priority')


class FeatureSegmentSerializer(serializers.ModelSerializer):
    segment = SegmentSerializerBasic()

    class Meta:
        model = FeatureSegment
        fields = ('segment', 'priority')


class FeatureSerializer(serializers.ModelSerializer):
    feature_segments = FeatureSegmentSerializer(many=True)

    class Meta:
        model = Feature
        fields = "__all__"


class FeatureStateSerializerFull(serializers.ModelSerializer):
    feature = CreateFeatureSerializer()
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
