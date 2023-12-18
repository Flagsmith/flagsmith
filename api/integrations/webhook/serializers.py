import typing

from django.db.models import Q
from flag_engine.segments.evaluator import evaluate_identity_in_segment
from rest_framework import serializers

from features.serializers import FeatureStateSerializerFull
from integrations.common.serializers import (
    BaseEnvironmentIntegrationModelSerializer,
)
from segments.models import Segment
from util.mappers.engine import map_identity_to_engine, map_segment_to_engine

from .models import WebhookConfiguration


class WebhookConfigurationSerializer(BaseEnvironmentIntegrationModelSerializer):
    class Meta:
        model = WebhookConfiguration
        fields = ("id", "url", "secret")


class SegmentSerializer(serializers.ModelSerializer):
    member = serializers.SerializerMethodField()

    class Meta:
        model = Segment
        fields = ("id", "name", "member")

    def get_member(self, obj: Segment) -> bool:
        engine_identity = map_identity_to_engine(
            self.context.get("identity"),
            with_overrides=False,
        )
        engine_segment = map_segment_to_engine(obj)
        return evaluate_identity_in_segment(
            identity=engine_identity,
            segment=engine_segment,
        )


class IntegrationFeatureStateSerializer(FeatureStateSerializerFull):
    def to_representation(self, instance):
        return_value = super().to_representation(instance)
        value = return_value["feature_state_value"]
        if value:
            return_value["percentage_allocation"] = self.get_percentage_allocation(
                value, instance
            )
        return return_value

    def get_percentage_allocation(self, value, instance) -> typing.Optional[float]:
        value_filter = {
            str: Q(multivariate_feature_option__string_value=value),
            int: Q(multivariate_feature_option__integer_value=value),
            bool: Q(multivariate_feature_option__boolean_value=value),
        }.get(type(value))
        mv_fs = instance.multivariate_feature_state_values.filter(value_filter).first()

        if mv_fs:
            return mv_fs.percentage_allocation
