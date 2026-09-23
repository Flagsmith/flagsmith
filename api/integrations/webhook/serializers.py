from typing import Any

from flag_engine.engine import get_evaluation_result
from rest_framework import serializers

from evaluation.mappers import map_environment_to_evaluation_context
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

    def get_member(self, obj: Segment) -> bool:
        identity = self.context["identity"]
        context = map_environment_to_evaluation_context(
            identity=identity,
            environment=identity.environment,
            segments=[obj],
        )
        result = get_evaluation_result(context)
        return bool(result["segments"])


class IntegrationFeatureStateSerializer(FeatureStateSerializerFull):
    def to_representation(self, instance: EvaluatedFeatureState) -> dict[str, Any]:
        representation: dict[str, Any] = super().to_representation(instance)
        if representation["feature_state_value"]:
            representation["percentage_allocation"] = get_split_weight(
                instance.evaluation_result
            )
        return representation
