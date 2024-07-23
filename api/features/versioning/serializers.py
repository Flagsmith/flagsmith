import typing

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api_keys.user import APIKeyUser
from features.serializers import (
    CustomCreateSegmentOverrideFeatureStateSerializer,
)
from features.versioning.models import EnvironmentFeatureVersion
from integrations.github.github import call_github_task
from segments.models import Segment
from users.models import FFAdminUser
from webhooks.webhooks import WebhookEventType


class CustomEnvironmentFeatureVersionFeatureStateSerializer(
    CustomCreateSegmentOverrideFeatureStateSerializer
):
    class Meta(CustomCreateSegmentOverrideFeatureStateSerializer.Meta):
        read_only_fields = (
            CustomCreateSegmentOverrideFeatureStateSerializer.Meta.read_only_fields
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
            "feature",
            "environment",
        )


class EnvironmentFeatureVersionRetrieveSerializer(EnvironmentFeatureVersionSerializer):
    previous_version_uuid = serializers.SerializerMethodField()

    class Meta(EnvironmentFeatureVersionSerializer.Meta):
        _fields = (
            "previous_version_uuid",
            "feature",
            "environment",
        )

        fields = EnvironmentFeatureVersionSerializer.Meta.fields + _fields

    def get_previous_version_uuid(
        self, environment_feature_version: EnvironmentFeatureVersion
    ) -> str | None:
        previous_version = environment_feature_version.get_previous_version()
        if not previous_version:
            return None
        return str(previous_version.uuid)


class EnvironmentFeatureVersionCreateSerializer(EnvironmentFeatureVersionSerializer):
    feature_states_to_create = CustomEnvironmentFeatureVersionFeatureStateSerializer(
        many=True,
        allow_null=True,
        required=False,
        help_text=(
            "Array of feature states that will be created in the new version. "
            "Note: these can only include segment overrides."
        ),
        write_only=True,
    )
    feature_states_to_update = CustomEnvironmentFeatureVersionFeatureStateSerializer(
        many=True,
        allow_null=True,
        required=False,
        help_text="Array of feature states to update in the new version.",
        write_only=True,
    )
    segment_ids_to_delete_overrides = serializers.ListSerializer(
        child=serializers.IntegerField(),
        required=False,
        allow_null=True,
        help_text="List of segment ids for which the segment overrides will be removed in the new version.",
        write_only=True,
    )
    publish_immediately = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Boolean to confirm whether the new version should be publish immediately or not.",
        write_only=True,
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

    def create(
        self, validated_data: dict[str, typing.Any]
    ) -> EnvironmentFeatureVersion:
        # Note that we use self.initial_data below for handling the feature states
        # since we want the raw data (rather than the serialized ORM objects) to pass
        # into the serializers in the separate private methods used for modifying the
        # FeatureState objects. As such, we just want to blindly remove the non-model
        # attribute keys from the validated before calling super to create the version.
        for field_name in self.Meta.non_model_fields:
            validated_data.pop(field_name, None)

        version = super().create(validated_data)

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
                {
                    "message": "Cannot create FeatureState objects that are not segment overrides."
                }
            )

        segment_id = feature_state["feature_segment"]["segment"]
        if (
            existing_segment_override := version.feature_states.filter(
                feature_segment__segment_id=segment_id
            )
            .select_related("feature_segment__segment")
            .first()
        ):
            raise serializers.ValidationError(
                {
                    "message": "An unresolvable conflict occurred: "
                    "segment override already exists for segment '%s'"
                    % existing_segment_override.feature_segment.segment.name
                }
            )

        save_kwargs = {
            "feature": version.feature,
            "environment": version.environment,
            "environment_feature_version": version,
        }
        fs_serializer = CustomEnvironmentFeatureVersionFeatureStateSerializer(
            data=feature_state,
            context=save_kwargs,
        )
        fs_serializer.is_valid(raise_exception=True)
        fs_serializer.save(**save_kwargs)

    def _update_feature_state(
        self, feature_state: dict[str, typing.Any], version: EnvironmentFeatureVersion
    ) -> None:
        if self._is_segment_override(feature_state):
            segment_id = feature_state["feature_segment"]["segment"]
            try:
                instance = version.feature_states.get(
                    feature_segment__segment_id=segment_id
                )
            except ObjectDoesNotExist:
                # Note that the segment will always exist because, if it didn't,
                # it would have been picked up in the serializer validation.
                segment = Segment.objects.get(id=segment_id)
                raise serializers.ValidationError(
                    {
                        "message": "An unresolvable conflict occurred: "
                        "segment override does not exist for segment '%s'."
                        % segment.name
                    }
                )
            # Patch the id of the feature segment onto the feature state data so that
            # the serializer knows to update rather than try and create a new one.
            feature_state["feature_segment"]["id"] = instance.feature_segment_id
        else:
            instance = version.feature_states.get(feature_segment__isnull=True)

        # TODO: can this be simplified at all?
        for existing_mvfsv in instance.multivariate_feature_state_values.all():
            updated_mvfsv_dicts = feature_state.get(
                "multivariate_feature_state_values", []
            )
            updated_mvfsv_dict = next(
                filter(
                    lambda d: d["multivariate_feature_option"]
                    == existing_mvfsv.multivariate_feature_option_id,
                    updated_mvfsv_dicts,
                ),
                None,
            )
            if updated_mvfsv_dict:
                updated_mvfsv_dict["id"] = existing_mvfsv.id

        fs_serializer = CustomEnvironmentFeatureVersionFeatureStateSerializer(
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
        version.feature_segments.filter(segment_id__in=segment_ids).delete()

    def _is_segment_override(self, feature_state: dict) -> bool:
        return feature_state.get("feature_segment") is not None


class EnvironmentFeatureVersionPublishSerializer(serializers.Serializer):
    live_from = serializers.DateTimeField(required=False)

    def save(self, **kwargs):
        live_from = self.validated_data.get("live_from")

        request = self.context["request"]

        published_by = None
        published_by_api_key = None

        if isinstance(request.user, FFAdminUser):
            published_by = request.user
        elif isinstance(request.user, APIKeyUser):
            published_by_api_key = request.user.key

        self.instance.publish(
            live_from=live_from,
            published_by=published_by,
            published_by_api_key=published_by_api_key,
        )
        return self.instance


class EnvironmentFeatureVersionQuerySerializer(serializers.Serializer):
    is_live = serializers.BooleanField(allow_null=True, required=False, default=None)
