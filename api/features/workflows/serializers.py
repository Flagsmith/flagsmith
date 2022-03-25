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


class UpdateChangeRequestFeatureStateSerializer(WritableNestedModelSerializer):
    feature_state_value = FeatureStateValueSerializer(required=False)
    multivariate_feature_state_values = MultivariateFeatureStateValueSerializer(
        many=True, required=False
    )

    class Meta:
        model = FeatureState
        fields = (
            "id",
            "feature",
            "feature_segment",
            "enabled",
            "feature_state_value",
            "multivariate_feature_state_values",
            "live_from",
        )
        read_only_fields = ("id",)


class CreateChangeRequestFeatureStateSerializer(
    UpdateChangeRequestFeatureStateSerializer
):
    class Meta(UpdateChangeRequestFeatureStateSerializer.Meta):
        read_only_fields = (
            UpdateChangeRequestFeatureStateSerializer.Meta.read_only_fields
            + ("multivariate_feature_state_values",)
        )


class ChangeRequestUpdateSerializer(WritableNestedModelSerializer):
    feature_states = UpdateChangeRequestFeatureStateSerializer(many=True)
    approvals = ChangeRequestApprovalSerializer(many=True, required=False)

    class Meta:
        model = ChangeRequest
        fields = (
            "id",
            "created_at",
            "updated_at",
            "title",
            "description",
            "feature_states",
            "deleted_at",
            "environment",
            "committed_at",
            "approvals",
            "user",
            "committed_by",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "user",
            "environment",
            "committed_at",
            "committed_by",
            "deleted_at",
        )


class ChangeRequestCreateSerializer(ChangeRequestUpdateSerializer):
    feature_states = CreateChangeRequestFeatureStateSerializer(many=True)

    def _get_save_kwargs(self, field_name):
        kwargs = super()._get_save_kwargs(field_name)
        if field_name == "feature_states":
            environment = self._save_kwargs["environment"]
            kwargs.update(environment=environment, version=None)
        return kwargs


class ChangeRequestListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeRequest
        fields = (
            "id",
            "created_at",
            "updated_at",
            "title",
            "description",
            "user",
            "committed_at",
            "committed_by",
            "deleted_at",
        )
        read_only_fields = fields


class ChangeRequestRetrieveSerializer(serializers.ModelSerializer):
    approvals = ChangeRequestApprovalSerializer(many=True)
    is_approved = serializers.SerializerMethodField()
    feature_states = CreateChangeRequestFeatureStateSerializer(many=True)

    class Meta:
        model = ChangeRequest
        fields = (
            "id",
            "created_at",
            "updated_at",
            "environment",
            "title",
            "description",
            "feature_states",
            "user",
            "committed_at",
            "committed_by",
            "deleted_at",
            "approvals",
            "is_approved",
            "is_committed",
        )
        read_only_fields = fields

    def get_is_approved(self, instance):  # noqa
        return instance.is_approved()


class ChangeRequestListQuerySerializer(serializers.Serializer):
    include_committed = serializers.BooleanField(
        required=False,
        help_text="Include change requests that have already been committed.",
        default=False,
    )
    search = serializers.CharField(
        required=False, help_text="Fuzzy search across Change Request titles."
    )
