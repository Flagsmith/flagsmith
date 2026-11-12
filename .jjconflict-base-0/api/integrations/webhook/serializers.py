from functools import cached_property
from typing import Any

from rest_framework import serializers

from evaluation.results import get_split_weight
from evaluation.types import EvaluatedFeatureState
from features.serializers import FeatureStateSerializerFull
from integrations.common.serializers import (
    BaseEnvironmentIntegrationModelSerializer,
)
from segments.models import Segment

from .models import WebhookConfiguration


class WebhookConfigurationSerializer(BaseEnvironmentIntegrationModelSerializer):
    class Meta:
        model = WebhookConfiguration
        fields = ("id", "url", "secret")


class SegmentSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    member = serializers.SerializerMethodField()

    class Meta:
        model = Segment
        fields = ("id", "name", "member")

    @cached_property
    def _member_segment_ids(self) -> set[int]:
        return {segment.pk for segment in self.context["identity"].get_segments()}

    def get_member(self, obj: Segment) -> bool:
        return obj.pk in self._member_segment_ids


class IntegrationFeatureStateSerializer(FeatureStateSerializerFull):
    def to_representation(self, instance: EvaluatedFeatureState) -> dict[str, Any]:
        representation: dict[str, Any] = super().to_representation(instance)
        if representation["feature_state_value"]:
            representation["percentage_allocation"] = get_split_weight(
                instance.evaluation_result
            )
        return representation
