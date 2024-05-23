from rest_framework import serializers

from features.serializers import CreateSegmentOverrideFeatureStateSerializer
from features.versioning.models import EnvironmentFeatureVersion
from integrations.github.github import call_github_task
from users.models import FFAdminUser
from webhooks.webhooks import WebhookEventType


class EnvironmentFeatureVersionFeatureStateSerializer(
    CreateSegmentOverrideFeatureStateSerializer
):
    class Meta(CreateSegmentOverrideFeatureStateSerializer.Meta):
        read_only_fields = (
            CreateSegmentOverrideFeatureStateSerializer.Meta.read_only_fields
            + ("feature",)
        )

    def save(self, **kwargs):
        response = super().save(**kwargs)

        feature_state = self.instance
        if (
            not feature_state.identity_id
            and feature_state.feature.external_resources.exists()
            and feature_state.environment.project.github_project.exists()
            and feature_state.environment.project.organisation.github_config.exists()
        ):

            call_github_task(
                organisation_id=feature_state.environment.project.organisation_id,
                type=WebhookEventType.FLAG_UPDATED.value,
                feature=feature_state.feature,
                segment_name=None,
                url=None,
                feature_states=[feature_state],
            )

        return response


class EnvironmentFeatureVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvironmentFeatureVersion
        fields = (
            "created_at",
            "updated_at",
            "published",
            "live_from",
            "uuid",
            "is_live",
            "published_by",
            "created_by",
            "description",
        )
        read_only_fields = (
            "updated_at",
            "created_at",
            "published",
            "uuid",
            "is_live",
            "published_by",
            "created_by",
        )


class EnvironmentFeatureVersionCreateSerializer(EnvironmentFeatureVersionSerializer):
    feature_states_to_create = EnvironmentFeatureVersionFeatureStateSerializer(
        many=True,
        allow_null=True,
        required=False,
        help_text=(
            "Array of feature states that will be created in the new version. "
            "Note: these can only include segment overrides."
        ),
    )
    feature_states_to_update = EnvironmentFeatureVersionFeatureStateSerializer(
        many=True,
        allow_null=True,
        required=False,
        help_text="Array of feature states to update in the new version.",
    )
    segment_ids_to_delete_overrides = serializers.ListSerializer(
        child=serializers.IntegerField(),
        required=False,
        allow_null=True,
        help_text="List of segment ids for which the segment overrides will be removed in the new version.",
    )
    publish_immediately = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Boolean to confirm whether the new version should be publish immediately or not.",
    )

    class Meta(EnvironmentFeatureVersionSerializer.Meta):
        fields = EnvironmentFeatureVersionSerializer.Meta.fields + (
            "feature_states_to_create",
            "feature_states_to_update",
            "segment_ids_to_delete_overrides",
            "publish_immediately",
        )
        non_model_fields = (
            "feature_states_to_create",
            "feature_states_to_update",
            "segment_ids_to_delete_overrides",
            "publish_immediately",
        )

    def create(self, validated_data):
        for field_name in self.Meta.non_model_fields:
            validated_data.pop(field_name, None)

        version = super().create(validated_data)

        # Note that we use self.initial_data for handling the feature states here
        # since we want the raw data (rather than the serialized ORM objects) to
        # pass into the serializers in the separate private methods used for modifying
        # the FeatureState objects.
        for feature_state_to_create in self.initial_data.get(
            "feature_states_to_create", []
        ):
            self._create_feature_state(
                {**feature_state_to_create, "environment": version.environment_id},
                version,
            )

        for feature_state_to_update in self.initial_data.get(
            "feature_states_to_update", []
        ):
            self._update_feature_state(feature_state_to_update, version)

        self._delete_feature_states(
            self.initial_data.get("segment_ids_to_delete_overrides", []), version
        )

        if self.validated_data.get("publish_immediately", False):
            request = self.context["request"]
            version.publish(
                published_by=(
                    request.user if isinstance(request.user, FFAdminUser) else None
                )
            )

        return version

    def _create_feature_state(
        self, feature_state: dict, version: EnvironmentFeatureVersion
    ) -> None:
        if not self._is_segment_override(feature_state):
            raise serializers.ValidationError(
                "Cannot create FeatureState objects that are not segment overrides."
            )

        segment_id = feature_state["feature_segment"]["segment"]
        if version.feature_states.filter(
            feature_segment__segment_id=segment_id
        ).exists():
            raise serializers.ValidationError(
                "Segment override already exists for Segment %d", segment_id
            )

        fs_serializer = EnvironmentFeatureVersionFeatureStateSerializer(
            data=feature_state,
            context={
                "feature": version.feature,
                "environment": version.environment,
                "environment_feature_version": version,
            },
        )
        fs_serializer.is_valid(raise_exception=True)
        fs_serializer.save(
            environment_feature_version=version,
            environment=version.environment,
            feature=version.feature,
        )

    def _update_feature_state(
        self, feature_state: dict, version: EnvironmentFeatureVersion
    ) -> None:
        if self._is_segment_override(feature_state):
            instance = version.feature_states.get(
                feature_segment__segment_id=feature_state["feature_segment"]["segment"]
            )
            # Patch the id of the feature segment onto the feature state data so that
            # the serializer knows to update rather than try and create a new one.
            feature_state["feature_segment"]["id"] = instance.feature_segment_id
        else:
            instance = version.feature_states.get(feature_segment__isnull=True)

        fs_serializer = EnvironmentFeatureVersionFeatureStateSerializer(
            instance=instance,
            data=feature_state,
            context={
                "feature": version.feature,
                "environment": version.environment,
                "environment_feature_version": version,
            },
        )
        fs_serializer.is_valid(raise_exception=True)
        fs_serializer.save(
            environment_feature_version=version, environment=version.environment
        )

    def _delete_feature_states(
        self, segment_ids: list[int], version: EnvironmentFeatureVersion
    ) -> None:
        version.feature_states.filter(
            feature_segment__segment_id__in=segment_ids
        ).delete()

    def _is_segment_override(self, feature_state: dict) -> bool:
        return feature_state.get("feature_segment") is not None


class EnvironmentFeatureVersionPublishSerializer(serializers.Serializer):
    live_from = serializers.DateTimeField(required=False)

    def save(self, **kwargs):
        live_from = self.validated_data.get("live_from")

        request = self.context["request"]
        published_by = request.user if isinstance(request.user, FFAdminUser) else None

        self.instance.publish(live_from=live_from, published_by=published_by)
        return self.instance


class EnvironmentFeatureVersionQuerySerializer(serializers.Serializer):
    is_live = serializers.BooleanField(allow_null=True, required=False, default=None)
