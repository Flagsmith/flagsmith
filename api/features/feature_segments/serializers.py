from rest_framework import serializers

from features.models import FeatureSegment


class FeatureSegmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureSegment
        fields = ("id", "uuid", "feature", "segment", "environment", "priority")
        read_only_fields = ("id", "uuid", "priority")

    def validate(self, data):
        data = super().validate(data)
        segment = data["segment"]
        if segment.feature is not None and segment.feature != data["feature"]:
            raise serializers.ValidationError(
                {
                    "feature": "Can only create segment override(using this segment) for feature %d"
                    % segment.feature.id,
                }
            )

        return data


class FeatureSegmentQuerySerializer(serializers.Serializer):
    environment = serializers.IntegerField()
    feature = serializers.IntegerField()


class FeatureSegmentListSerializer(serializers.ModelSerializer):
    segment_name = serializers.SerializerMethodField()
    is_feature_specific = serializers.SerializerMethodField()

    class Meta:
        model = FeatureSegment
        fields = (
            "id",
            "uuid",
            "segment",
            "priority",
            "environment",
            "segment_name",
            "is_feature_specific",
        )
        read_only_fields = (
            "id",
            "uuid",
            "segment",
            "priority",
            "environment",
            "segment_name",
            "is_feature_specific",
        )

    def get_value(self, instance):
        return instance.get_value()

    def get_segment_name(self, instance: FeatureSegment) -> str:
        return instance.segment.name

    def get_is_feature_specific(self, instance: FeatureSegment) -> bool:
        return instance.segment.feature is not None


class FeatureSegmentChangePrioritiesListSerializer(serializers.ListSerializer):
    def validate(self, attrs):
        validated_attrs = super().validate(attrs)
        feature_segments = list(
            FeatureSegment.objects.filter(
                id__in=[item["id"] for item in validated_attrs]
            )
        )

        # TODO: what if length == 0?
        if not len(feature_segments) == len(attrs):
            raise serializers.ValidationError(
                "Some of the provided ids were not found."
            )

        environments = set()
        features = set()

        for feature_segment in feature_segments:
            environments.add(feature_segment.environment)
            features.add(feature_segment.feature)

        if not len(environments) == len(features) == 1:
            raise serializers.ValidationError(
                "All feature segments must belong to the same feature & environment."
            )

        return validated_attrs

    def create(self, validated_data):
        id_priority_pairs = FeatureSegment.to_id_priority_tuple_pairs(validated_data)
        return FeatureSegment.update_priorities(id_priority_pairs)


class FeatureSegmentChangePrioritiesSerializer(serializers.ModelSerializer):
    priority = serializers.IntegerField(
        min_value=0, help_text="Value to change the feature segment's priority to."
    )
    id = serializers.IntegerField()

    class Meta:
        model = FeatureSegment
        fields = ("id", "priority")
        list_serializer_class = FeatureSegmentChangePrioritiesListSerializer
