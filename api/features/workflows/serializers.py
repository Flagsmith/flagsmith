from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from features.models import FeatureState
from features.multivariate.serializers import (
    MultivariateFeatureStateValueSerializer,
)
from features.serializers import FeatureStateValueSerializer
from features.workflows.models import ChangeRequest, ChangeRequestApproval


class ChangeRequestApprovalSerializer(WritableNestedModelSerializer):
    class Meta:
        model = ChangeRequestApproval
        fields = ("id", "user", "required", "approved_at")
        read_only_fields = ("id", "approved_at")


class ToFeatureStateSerializer(WritableNestedModelSerializer):
    feature_state_value = FeatureStateValueSerializer(required=False)
    multivariate_feature_state_values = MultivariateFeatureStateValueSerializer(
        many=True, required=False
    )

    class Meta:
        model = FeatureState
        fields = (
            "id",
            "enabled",
            "feature_state_value",
            "multivariate_feature_state_values",
            "live_from",
        )
        read_only_fields = ("id",)


class ChangeRequestSerializer(WritableNestedModelSerializer):
    to_feature_state = ToFeatureStateSerializer()
    approvals = ChangeRequestApprovalSerializer(many=True, required=False)

    class Meta:
        model = ChangeRequest
        fields = (
            "id",
            "created_at",
            "updated_at",
            "title",
            "description",
            "from_feature_state",
            "to_feature_state",
            "deleted_at",
            "committed_at",
            "approvals",
            "user",
            "committed_by",
        )
        read_only_fields = ("id", "created_at", "updated_at", "user", "committed_by")

    def _get_save_kwargs(self, field_name):
        kwargs = super()._get_save_kwargs(field_name)
        if field_name == "to_feature_state":
            from_feature_state = self.validated_data["from_feature_state"]
            kwargs.update(
                feature=from_feature_state.feature,
                environment=from_feature_state.environment,
                feature_segment=from_feature_state.feature_segment,
                identity=from_feature_state.identity,
                version=None,
            )
        return kwargs


class ChangeRequestListQuerySerializer(serializers.Serializer):
    environment = serializers.IntegerField(
        required=True, help_text="ID of the environment to filter by"
    )
