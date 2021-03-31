from rest_framework import serializers

from features.models import FeatureSegment
from features.value_types import STRING


class FeatureSegmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureSegment
        fields = ("id", "feature", "segment", "environment", "priority")
        read_only_fields = ("id", "priority")


class FeatureSegmentQuerySerializer(serializers.Serializer):
    environment = serializers.IntegerField()
    feature = serializers.IntegerField()


class FeatureSegmentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureSegment
        fields = ("id", "segment", "priority", "environment")
        read_only_fields = ("id", "segment", "priority", "environment")

    def get_value(self, instance):
        return instance.get_value()


class FeatureSegmentChangePrioritiesSerializer(serializers.Serializer):
    priority = serializers.IntegerField(
        min_value=0, help_text="Value to change the feature segment's priority to."
    )
    id = serializers.IntegerField()

    def create(self, validated_data):
        try:
            instance = FeatureSegment.objects.get(id=validated_data["id"])
            return self.update(instance, validated_data)
        except FeatureSegment.DoesNotExist:
            raise serializers.ValidationError(
                "No feature segment exists with id: %s" % validated_data["id"]
            )

    def update(self, instance, validated_data):
        instance.to(validated_data["priority"])
        return instance
