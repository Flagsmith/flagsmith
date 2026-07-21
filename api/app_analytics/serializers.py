from typing import TYPE_CHECKING, Any, get_args

from common.core.utils import using_database_replica
from django.conf import settings
from rest_framework import serializers

from app_analytics.cache import FeatureEvaluationCache
from app_analytics.constants import LABELS
from app_analytics.mappers import map_request_to_labels
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
    """
    Expect label fields in the query string
    and envelope them under a `labels_filter` key.

    This is to simplify the query syntax for filtering by labels
    while avoiding variable keyword arguments in the app_analytics
    service interfaces.
    """

    def get_fields(self) -> dict[str, serializers.Field[Any, Any, Any, Any]]:
        return {**super().get_fields(), **_get_label_fields()}

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
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
            using_database_replica(FeatureState.objects)
            .filter(
                environment=request.environment,
                feature_segment=None,
                identity=None,
            )
            .values_list("feature__name", flat=True)
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


class SDKAnalyticsFlagsV1Serializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for the V1 SDK analytics flags endpoint.

    Accepts a flat ``{feature_name: evaluation_count}`` dict.
    Unknown feature names and non-integer counts are silently skipped.
    """

    def to_internal_value(self, data: Any) -> dict[str, int]:
        if not isinstance(data, dict):
            raise serializers.ValidationError(
                {"non_field_errors": ["Expected a JSON object."]}
            )
        return {
            name: count
            for name, count in data.items()
            if isinstance(name, str) and type(count) is int
        }

    def validate(self, attrs: dict[str, int]) -> dict[str, int]:
        request = self.context["request"]
        environment_feature_names = set(
            using_database_replica(FeatureState.objects)
            .filter(
                environment=request.environment,
                feature_segment=None,
                identity=None,
            )
            .values_list("feature__name", flat=True)
        )
        return {
            name: count
            for name, count in attrs.items()
            if name in environment_feature_names
        }

    def save(self, **kwargs: Any) -> None:
        environment: Environment = kwargs["environment"]
        cache: FeatureEvaluationCache = kwargs["cache"]
        request = self.context["request"]
        labels = map_request_to_labels(request)
        for feature_name, evaluation_count in self.validated_data.items():
            cache.track_feature_evaluation(
                environment_id=environment.id,
                feature_name=feature_name,
                evaluation_count=evaluation_count,
                labels=labels,
            )


def _get_label_fields() -> dict[str, serializers.Field[Any, Any, Any, Any]]:
    return {
        str(label): serializers.CharField(allow_null=True, required=False)
        for label in LABELS
    }
