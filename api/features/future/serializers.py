"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from typing import get_args

from rest_framework import serializers

from features.feature_states.exceptions import FeatureValueError
from features.feature_states.models import FeatureValueType
from features.feature_types import MULTIVARIATE
from features.future.services import check_variants
from features.future.types import (
    EnvironmentDefaultRequest,
    FlagValue,
    SegmentOverrideRequest,
    UpdateFlagRequest,
    Variant,
)
from features.models import Feature, FeatureStateValue
from segments.models import Segment


class FlagValueSerializer(serializers.Serializer[FlagValue]):
    """A flag value, typed by the caller so it survives the round trip as a string."""

    type = serializers.ChoiceField(choices=get_args(FeatureValueType))
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
    value = FlagValueSerializer(
        required=False,
        allow_null=True,
        help_text="Null clears the value.",
    )
    variants = VariantSerializer(many=True, required=False)

    def validate_value(self, value: FlagValue | None) -> FlagValue | None:
        if value is None:
            return None
        try:
            FeatureStateValue().set_value(value["value"], value["type"])
        except FeatureValueError as error:
            raise serializers.ValidationError(str(error)) from error
        return value

    def validate_variants(self, variants: list[Variant]) -> list[Variant]:
        check_variants(self.context["feature"], [variants])
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
