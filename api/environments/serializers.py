import typing

from common.metadata.serializers import (
    MetadataSerializer,
    SerializerWithMetadata,
)
from django.db import models
from rest_framework import serializers

from environments.models import Environment, EnvironmentAPIKey, Webhook
from features.serializers import FeatureStateSerializerFull
from organisations.models import Subscription
from organisations.subscriptions.serializers.mixins import (
    ReadOnlyIfNotValidPlanMixin,
)
from projects.models import Project
from projects.serializers import ProjectListSerializer
from util.drf_writable_nested.serializers import (
    DeleteBeforeUpdateWritableNestedModelSerializer,
)


class EnvironmentSerializerFull(serializers.ModelSerializer):  # type: ignore[type-arg]
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
            "is_creating",
        )


class EnvironmentSerializerLight(serializers.ModelSerializer):  # type: ignore[type-arg]
    use_mv_v2_evaluation = serializers.SerializerMethodField()

    class Meta:
        model = Environment
        fields = (
            "id",
            "uuid",
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
            "use_v2_feature_versioning",
            "use_identity_overrides_in_local_eval",
            "is_creating",
        )
        read_only_fields = ("use_v2_feature_versioning",)

    def get_use_mv_v2_evaluation(self, instance: Environment) -> bool:
        """
        To avoid breaking the API, we return this field as well.

        Warning: this will still mean that sending the `use_mv_v2_evaluation` field
        (e.g. in a PUT request) will not behave as expected but, since this is a minor
        issue, I think we can ignore.
        """
        return instance.use_identity_composite_key_for_hashing  # type: ignore[no-any-return]


class EnvironmentSerializerWithMetadata(
    SerializerWithMetadata,
    DeleteBeforeUpdateWritableNestedModelSerializer,
    EnvironmentSerializerLight,
):
    metadata = MetadataSerializer(required=False, many=True)

    class Meta(EnvironmentSerializerLight.Meta):
        fields = EnvironmentSerializerLight.Meta.fields + ("metadata",)  # type: ignore[assignment]

    def get_project(
        self,
        validated_data: dict[str, typing.Any] | None = None,
    ) -> Project:
        if self.instance:
            return self.instance.project  # type: ignore[no-any-return,union-attr]
        elif validated_data and "project" in validated_data:
            return validated_data["project"]  # type: ignore[no-any-return]

        raise serializers.ValidationError(
            "Unable to retrieve project for metadata validation."
        )

    def update(
        self, instance: models.Model, validated_data: dict[str, typing.Any]
    ) -> Environment:
        metadata_items = validated_data.pop("metadata", [])
        environment = super().update(instance, validated_data)
        self.update_metadata(environment, metadata_items)  # type: ignore[no-untyped-call]
        environment.refresh_from_db()
        assert isinstance(environment, Environment)
        return environment


class EnvironmentRetrieveSerializerWithMetadata(EnvironmentSerializerWithMetadata):
    total_segment_overrides = serializers.IntegerField()

    class Meta(EnvironmentSerializerWithMetadata.Meta):
        fields = EnvironmentSerializerWithMetadata.Meta.fields + (  # type: ignore[has-type]
            "total_segment_overrides",
        )
        read_only_fields = ("total_segment_overrides",)


class CreateUpdateEnvironmentSerializer(
    ReadOnlyIfNotValidPlanMixin, EnvironmentSerializerWithMetadata
):
    invalid_plans = ("free",)
    field_names = ("minimum_change_request_approvals",)

    class Meta(EnvironmentSerializerWithMetadata.Meta):
        validators = [
            serializers.UniqueTogetherValidator(  # type: ignore[attr-defined]
                queryset=EnvironmentSerializerWithMetadata.Meta.model.objects.all(),
                fields=("name", "project"),
                message="An environment with this name already exists.",
            )
        ]

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
            return getattr(self.instance.project.organisation, "subscription", None)  # type: ignore[union-attr]

        return None


class CloneEnvironmentSerializer(EnvironmentSerializerLight):
    clone_feature_states_async = serializers.BooleanField(
        default=False,
        help_text="If True, the environment will be created immediately, but the feature states "
        "will be created asynchronously. Environment will have `is_creating: true` until "
        "this process is completed.",
        write_only=True,
    )

    class Meta:
        model = Environment
        fields = ("id", "name", "api_key", "project", "clone_feature_states_async")
        read_only_fields = ("id", "api_key", "project")

    def create(self, validated_data):  # type: ignore[no-untyped-def]
        name = validated_data.get("name")
        source_env = validated_data.get("source_env")
        clone_feature_states_async = validated_data.get("clone_feature_states_async")
        clone = source_env.clone(
            name, clone_feature_states_async=clone_feature_states_async
        )
        return clone


class WebhookSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Webhook
        fields = ("id", "url", "enabled", "created_at", "updated_at", "secret")
        read_only_fields = ("id", "created_at", "updated_at")


class EnvironmentAPIKeySerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = EnvironmentAPIKey
        fields = ("id", "key", "active", "created_at", "name", "expires_at")
        read_only_fields = ("id", "created_at", "key")
