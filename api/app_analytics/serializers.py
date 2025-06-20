from typing import TYPE_CHECKING, Any, get_args

from django.conf import settings
from rest_framework import serializers

from app_analytics.constants import LABELS
from app_analytics.tasks import (
    track_feature_evaluation_influxdb_v2,
    track_feature_evaluation_v2,
)
from app_analytics.types import Labels, PeriodType
from environments.models import Environment
from features.models import FeatureState

if TYPE_CHECKING:
    _SerializerType = serializers.Serializer[Any]
else:
    _SerializerType = object


class LabelsQuerySerializerMixin(_SerializerType):
    def get_fields(self) -> dict[str, serializers.Field[Any, Any, Any, Any]]:
        return {**super().get_fields(), **_get_label_fields()}

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Yank label filters from the top level and place them under a
        separate `labels_filter` key
        """
        attrs = super().validate(attrs)
        if labels_filter := {
            label: attrs.pop(label)
            for label in LABELS
            if label in attrs and attrs[label] is not None
        }:
            attrs["labels_filter"] = labels_filter
        return attrs


class LabelsSerializer(serializers.Serializer[Labels]):
    def get_fields(self) -> dict[str, serializers.Field[Any, Any, Any, Any]]:
        return _get_label_fields()


class UsageDataSerializer(serializers.Serializer):  # type: ignore[type-arg]
    flags = serializers.IntegerField()
    identities = serializers.IntegerField()
    traits = serializers.IntegerField()
    environment_document = serializers.IntegerField()
    day = serializers.CharField()
    labels = LabelsSerializer(allow_null=True, required=False)


class UsageDataQuerySerializer(LabelsQuerySerializerMixin, serializers.Serializer):  # type: ignore[type-arg]
    project_id = serializers.IntegerField(required=False)
    environment_id = serializers.IntegerField(required=False)
    period = serializers.ChoiceField(
        choices=get_args(PeriodType),
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

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
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

    def save(self, **kwargs: Any) -> None:
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


def _get_label_fields() -> dict[str, serializers.Field[Any, Any, Any, Any]]:
    return {
        str(label): serializers.CharField(allow_null=True, required=False)
        for label in LABELS
    }
