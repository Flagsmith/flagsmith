from drf_writable_nested import WritableNestedModelSerializer

from features.models import FeatureState
from features.serializers import FeatureStateValueSerializer
from features.workflows.models import ChangeRequest, ChangeRequestApproval


class ChangeRequestApprovalSerializer(WritableNestedModelSerializer):
    class Meta:
        model = ChangeRequestApproval
        fields = ("id", "user", "required", "approved_at")
        read_only_fields = ("id", "approved_at")


class ChangeRequestSerializer(WritableNestedModelSerializer):
    class ToFeatureStateSerializer(WritableNestedModelSerializer):
        """
        FeatureState serializer used only by ChangeRequest serializer (and hence
        declared locally).

        Expects the from_feature_state attribute to be set in the context by its parent.

        Uses the from_feature_state to set the feature, environment, feature_segment
        and identity attributes on the to_feature_state.
        """

        feature_state_value = FeatureStateValueSerializer(required=False)

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

        def save(self, **kwargs):
            if "from_feature_state" not in self.context:
                raise RuntimeError("`from_feature_state` must be set in context.")

            # set the environment, feature, feature_segment and identity attributes on
            # the to_feature_state by retrieving from from_feature_state
            # TODO: can this be handled better? For example:
            #  - should we make this an action on FS viewset?
            #  - or should this code live in the view?
            kwargs.update(
                {
                    attr: getattr(self.context["from_feature_state"], attr)
                    for attr in (
                        "feature",
                        "environment",
                        "feature_segment",
                        "identity",
                    )
                }
            )
            return super().save(**kwargs, version=None)

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
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        self.context["from_feature_state"] = validated_data["from_feature_state"]
        return validated_data
