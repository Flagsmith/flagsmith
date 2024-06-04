from rest_framework import serializers

from api_keys.user import APIKeyUser
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
