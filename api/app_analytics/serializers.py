import typing

from django.conf import settings
from rest_framework import serializers

from app_analytics.tasks import (
    track_feature_evaluation_influxdb_v2,
    track_feature_evaluation_v2,
)
from environments.models import Environment
from features.models import FeatureState

from .types import PERIOD_TYPE


class UsageDataSerializer(serializers.Serializer):  # type: ignore[type-arg]
    flags = serializers.IntegerField()
    identities = serializers.IntegerField()
    traits = serializers.IntegerField()
    environment_document = serializers.IntegerField()
    day = serializers.CharField()


class UsageDataQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    project_id = serializers.IntegerField(required=False)
    environment_id = serializers.IntegerField(required=False)
    period = serializers.ChoiceField(
        choices=typing.get_args(PERIOD_TYPE),
        allow_null=True,
        default=None,
        required=False,
    )


class UsageTotalCountSerializer(serializers.Serializer):  # type: ignore[type-arg]
    count = serializers.IntegerField()


class SDKAnalyticsFlagsSerializerDetail(serializers.Serializer):  # type: ignore[type-arg]
    feature_name = serializers.CharField()
    identity_identifier = serializers.CharField(required=False, default=None)
    enabled_when_evaluated = serializers.BooleanField()
    count = serializers.IntegerField()


class SDKAnalyticsFlagsSerializer(serializers.Serializer):  # type: ignore[type-arg]
    evaluations = SDKAnalyticsFlagsSerializerDetail(many=True)

    def validate(self, attrs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        request = self.context["request"]
        environment_feature_names = set(
            FeatureState.objects.filter(
                environment=request.environment,
                feature_segment=None,
                identity=None,
            ).values_list("feature__name", flat=True)
        )
        return {
            "evaluations": [
                evaluation
                for evaluation in attrs["evaluations"]
                if evaluation["feature_name"] in environment_feature_names
            ]
        }

    def save(self, **kwargs: typing.Any) -> typing.Any:
        environment: Environment = kwargs["environment"]

        if settings.USE_POSTGRES_FOR_ANALYTICS:
            track_feature_evaluation_v2.delay(
                args=(
                    environment.id,
                    self.validated_data["evaluations"],
                )
            )
        elif settings.INFLUXDB_TOKEN:
            track_feature_evaluation_influxdb_v2.delay(
                args=(
                    environment.id,
                    self.validated_data["evaluations"],
                )
            )
