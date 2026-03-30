import typing

from django.db.models import Q
from flag_engine.engine import get_evaluation_result
from rest_framework import serializers

from features.serializers import FeatureStateSerializerFull
from integrations.common.serializers import (
    BaseEnvironmentIntegrationModelSerializer,
)
from segments.models import Segment
from util.mappers.engine import map_environment_to_evaluation_context

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
    def to_representation(self, instance):  # type: ignore[no-untyped-def]
        return_value = super().to_representation(instance)
        value = return_value["feature_state_value"]
        if value:
            return_value["percentage_allocation"] = self.get_percentage_allocation(
                value, instance
            )
        return return_value

    def get_percentage_allocation(self, value, instance) -> typing.Optional[float]:  # type: ignore[no-untyped-def,return]  # noqa: E501
        value_filter = {
            str: Q(multivariate_feature_option__string_value=value),
            int: Q(multivariate_feature_option__integer_value=value),
            bool: Q(multivariate_feature_option__boolean_value=value),
        }.get(type(value))
        mv_fs = instance.multivariate_feature_state_values.filter(value_filter).first()

        if mv_fs:
            return mv_fs.percentage_allocation  # type: ignore[no-any-return]
