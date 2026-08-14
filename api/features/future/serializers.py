"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from rest_framework import serializers

from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureStateValue
from segments.models import Segment

from .types import (
    EnvironmentDefaultRequest,
    FlagValue,
    SegmentOverrideRequest,
    UpdateFlagRequest,
    Variant,
)


class FlagValueSerializer(serializers.Serializer[FlagValue]):
    """A flag value, typed by the caller so it survives the round trip as a string."""

    type = serializers.ChoiceField(choices=["string", "integer", "boolean"])
    value = serializers.CharField(allow_blank=True)


class VariantSerializer(serializers.Serializer[Variant]):
    """The share of an environment or segment a multivariate variant is served to."""

    id = serializers.IntegerField()
    weight = serializers.FloatField(min_value=0, max_value=100)


class SegmentReferenceSerializer(serializers.Serializer[Segment]):
    """A segment of the feature's project, referenced by an override."""

    id = serializers.IntegerField()

    def validate_id(self, id: int) -> int:
        feature: Feature = self.context["feature"]
        if not Segment.live_objects.filter(
            id=id, project_id=feature.project_id
        ).exists():
            raise serializers.ValidationError("Segment not found.")
        return id


class FlagStateSerializer(serializers.Serializer[dict[str, object]]):
    """What a flag serves somewhere in an environment."""

    enabled = serializers.BooleanField(required=False)
    value = FlagValueSerializer(required=False)
    variants = VariantSerializer(many=True, required=False)

    def validate_value(self, value: FlagValue) -> FlagValue:
        try:
            FeatureStateValue().set_value(value["value"], value["type"])
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value

    def validate_variants(self, variants: list[Variant]) -> list[Variant]:
        feature: Feature = self.context["feature"]
        if feature.type != MULTIVARIATE:
            raise serializers.ValidationError("Feature is not multivariate.")
        known_ids = set(feature.multivariate_options.values_list("id", flat=True))
        given_ids = {variant["id"] for variant in variants}
        if given_ids - known_ids:
            raise serializers.ValidationError("Variant not found.")
        if known_ids - given_ids:
            raise serializers.ValidationError("Must include all feature's variants.")
        if sum(variant["weight"] for variant in variants) > 100:
            raise serializers.ValidationError("Total weight must not exceed 100.")
        return variants


class EnvironmentDefaultSerializer(FlagStateSerializer):
    """What the flag serves to everyone the segment overrides do not match."""

    def validate(self, attrs: EnvironmentDefaultRequest) -> EnvironmentDefaultRequest:
        feature: Feature = self.context["feature"]
        if (
            self.context["replace"]
            and feature.type == MULTIVARIATE
            and "variants" not in attrs
        ):
            raise serializers.ValidationError(
                {"variants": ["Must include all feature's variants."]}
            )
        return attrs


class SegmentOverrideSerializer(FlagStateSerializer):
    """What the flag serves to the identities a segment matches."""

    segment = SegmentReferenceSerializer()
    priority = serializers.IntegerField(min_value=0, required=False)


class UpdateFlagSerializer(serializers.Serializer[UpdateFlagRequest]):
    """The parts of a flag a caller wants to write in one request."""

    environment_default = EnvironmentDefaultSerializer(required=False)
    segment_overrides = SegmentOverrideSerializer(many=True, required=False)

    def validate_segment_overrides(
        self, segment_overrides: list[SegmentOverrideRequest]
    ) -> list[SegmentOverrideRequest]:
        seen: set[int] = set()
        for override in segment_overrides:
            segment_id = override["segment"]["id"]
            if segment_id in seen:
                raise serializers.ValidationError(f"Duplicate segment: {segment_id}.")
            seen.add(segment_id)
        return segment_overrides
