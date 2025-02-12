from common.environments.permissions import MANAGE_SEGMENT_OVERRIDES
from common.features.serializers import (
    CreateSegmentOverrideFeatureSegmentSerializer,
)
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from features.feature_segments.limits import (
    SEGMENT_OVERRIDE_LIMIT_EXCEEDED_MESSAGE,
    exceeds_segment_override_limit,
)
from features.models import FeatureSegment


class FeatureSegmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureSegment
        fields = ("id", "uuid", "feature", "segment", "environment", "priority")
        read_only_fields = ("id", "uuid", "priority")

    def validate(self, data):
        data = super().validate(data)
        if exceeds_segment_override_limit(data["environment"]):
            raise serializers.ValidationError(
                {"environment": SEGMENT_OVERRIDE_LIMIT_EXCEEDED_MESSAGE}
            )

        segment = data["segment"]
        if segment.feature is not None and segment.feature != data["feature"]:
            raise serializers.ValidationError(
                {
                    "feature": "Can only create segment override(using this segment) for feature %d"
                    % segment.feature.id,
                }
            )

        return data


class CustomCreateSegmentOverrideFeatureSegmentSerializer(
    CreateSegmentOverrideFeatureSegmentSerializer
):
    # Since the `priority` field on the FeatureSegment model is set to editable=False
    # (to adhere to the django-ordered-model functionality), we redefine the priority
    # field here, and use it manually in the save method.
    priority = serializers.IntegerField(min_value=0, required=False)

    @transaction.atomic()
    def save(self, **kwargs) -> FeatureSegment:
        """
        Note that this method is marked as atomic since a lot of additional validation is
        performed in the call to super. If that fails, we want to roll the changes made by
        `collision.to` back.
        """

        priority: int | None = self.validated_data.get("priority", None)

        if kwargs["environment"].use_v2_feature_versioning:  # pragma: no cover
            assert (
                kwargs["environment_feature_version"] is not None
            ), "Must provide environment_feature_version for environment using v2 versioning"

        if priority is not None:
            collision_qs = FeatureSegment.objects.filter(
                environment=kwargs["environment"],
                feature=kwargs["feature"],
                environment_feature_version=kwargs.get("environment_feature_version"),
                priority=priority,
            )
            if self.instance is not None:
                collision_qs = collision_qs.exclude(id=self.instance.id)
            collision = collision_qs.first()
            if collision:
                # Since there is no unique clause on the priority field, if a priority
                # is set, it will just save the feature segment and not move others
                # down. This ensures that the incoming priority space is 'free'.
                collision.to(priority + 1)

        return super().save(**kwargs)


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
        if len(validated_attrs) == 0:
            return validated_attrs

        feature_segments = list(
            FeatureSegment.objects.filter(
                id__in=[item["id"] for item in validated_attrs]
            )
            .select_related("environment")
            .prefetch_related("feature_states")
        )

        if not len(feature_segments) == len(attrs):
            raise serializers.ValidationError(
                "Some of the provided ids were not found."
            )

        environment_ids = set()
        feature_ids = set()

        for feature_segment in feature_segments:
            environment_ids.add(feature_segment.environment_id)
            feature_ids.add(feature_segment.feature_id)

        if not len(environment_ids) == len(feature_ids) == 1:
            raise serializers.ValidationError(
                "All feature segments must belong to the same feature & environment."
            )

        environment = feature_segments[0].environment

        if not self.context["request"].user.has_environment_permission(
            MANAGE_SEGMENT_OVERRIDES, environment
        ):
            raise PermissionDenied("You do not have permission to perform this action.")

        if environment.use_v2_feature_versioning:
            self._validate_unique_environment_feature_version(feature_segments)

        return validated_attrs

    def create(self, validated_data):
        id_priority_pairs = FeatureSegment.to_id_priority_tuple_pairs(validated_data)
        return FeatureSegment.update_priorities(id_priority_pairs)

    @staticmethod
    def _validate_unique_environment_feature_version(
        feature_segments: list[FeatureSegment],
    ) -> None:
        feature_states = []
        for feature_segment in feature_segments:
            feature_states.extend(feature_segment.feature_states.all())
        unique_versions = {
            feature_state.environment_feature_version_id
            for feature_state in feature_states
        }
        if not len(unique_versions) == 1:
            raise serializers.ValidationError(
                "All feature segments must be associated with the same environment feature version."
            )


class FeatureSegmentChangePrioritiesSerializer(serializers.ModelSerializer):
    priority = serializers.IntegerField(
        min_value=0, help_text="Value to change the feature segment's priority to."
    )
    id = serializers.IntegerField()

    class Meta:
        model = FeatureSegment
        fields = ("id", "priority")
        list_serializer_class = FeatureSegmentChangePrioritiesListSerializer
