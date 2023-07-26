import typing

from rest_framework import serializers

from environments.models import Environment, EnvironmentAPIKey, Webhook
from features.serializers import FeatureStateSerializerFull
from metadata.serializers import MetadataSerializer, SerializerWithMetadata
from organisations.models import Organisation, Subscription
from organisations.subscriptions.serializers.mixins import (
    ReadOnlyIfNotValidPlanMixin,
)
from projects.models import Project
from projects.serializers import ProjectListSerializer
from util.drf_writable_nested.serializers import (
    DeleteBeforeUpdateWritableNestedModelSerializer,
)


class EnvironmentSerializerFull(serializers.ModelSerializer):
    feature_states = FeatureStateSerializerFull(many=True)
    project = ProjectListSerializer()

    class Meta:
        model = Environment
        fields = (
            "id",
            "name",
            "feature_states",
            "project",
            "api_key",
            "minimum_change_request_approvals",
            "allow_client_traits",
        )


class EnvironmentSerializerLight(serializers.ModelSerializer):
    use_mv_v2_evaluation = serializers.SerializerMethodField()

    class Meta:
        model = Environment
        fields = (
            "id",
            "name",
            "api_key",
            "description",
            "project",
            "minimum_change_request_approvals",
            "allow_client_traits",
            "banner_text",
            "banner_colour",
            "hide_disabled_flags",
            "use_mv_v2_evaluation",
            "use_identity_composite_key_for_hashing",
            "hide_sensitive_data",
        )

    def get_use_mv_v2_evaluation(self, instance: Environment) -> bool:
        """
        To avoid breaking the API, we return this field as well.

        Warning: this will still mean that sending the `use_mv_v2_evaluation` field
        (e.g. in a PUT request) will not behave as expected but, since this is a minor
        issue, I think we can ignore.
        """
        return instance.use_identity_composite_key_for_hashing


class EnvironmentRetrieveSerializerLight(EnvironmentSerializerLight):
    class Meta(EnvironmentSerializerLight.Meta):
        fields = EnvironmentSerializerLight.Meta.fields + ("total_segment_overrides",)


class EnvironmentSerializerWithMetadata(
    SerializerWithMetadata,
    DeleteBeforeUpdateWritableNestedModelSerializer,
    EnvironmentRetrieveSerializerLight,
):
    metadata = MetadataSerializer(required=False, many=True)

    class Meta(EnvironmentRetrieveSerializerLight.Meta):
        fields = EnvironmentRetrieveSerializerLight.Meta.fields + ("metadata",)

    def get_organisation_from_validated_data(self, validated_data) -> Organisation:
        return validated_data.get("project").organisation

    def get_project_from_validated_data(self, validated_data) -> Project:
        return validated_data.get("project")


class CreateUpdateEnvironmentSerializer(
    ReadOnlyIfNotValidPlanMixin, EnvironmentSerializerWithMetadata
):
    invalid_plans = ("free",)
    field_names = ("minimum_change_request_approvals",)

    def get_subscription(self) -> typing.Optional[Subscription]:
        view = self.context["view"]

        if view.action == "create":
            # handle `project` not being part of the data
            # When request comes from yasg2(as part of schema generation)
            project_id = view.request.data.get("project")
            if not project_id:
                return None

            project = Project.objects.select_related(
                "organisation", "organisation__subscription"
            ).get(id=project_id)

            return getattr(project.organisation, "subscription", None)
        elif view.action in ("update", "partial_update"):
            return getattr(self.instance.project.organisation, "subscription", None)

        return None


class CloneEnvironmentSerializer(EnvironmentSerializerLight):
    class Meta:
        model = Environment
        fields = ("id", "name", "api_key", "project")
        read_only_fields = ("id", "api_key", "project")

    def create(self, validated_data):
        name = validated_data.get("name")
        source_env = validated_data.get("source_env")
        clone = source_env.clone(name)
        return clone


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ("id", "url", "enabled", "created_at", "updated_at", "secret")
        read_only_fields = ("id", "created_at", "updated_at")


class EnvironmentAPIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvironmentAPIKey
        fields = ("id", "key", "active", "created_at", "name", "expires_at")
        read_only_fields = ("id", "created_at", "key")
