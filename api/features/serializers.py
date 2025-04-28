import typing
from datetime import datetime

import django.core.exceptions
from common.features.multivariate.serializers import (
    MultivariateFeatureStateValueSerializer,
)
from common.features.serializers import (
    CreateSegmentOverrideFeatureStateSerializer,
    FeatureStateValueSerializer,
)
from common.metadata.serializers import (
    MetadataSerializer,
    SerializerWithMetadata,
)
from django.db import models
from drf_writable_nested import (  # type: ignore[attr-defined]
    WritableNestedModelSerializer,
)
from drf_yasg.utils import swagger_serializer_method  # type: ignore[import-untyped]
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from environments.identities.models import Identity
from environments.sdk.serializers_mixins import (
    HideSensitiveFieldsSerializerMixin,
)
from integrations.github.constants import GitHubEventType
from integrations.github.github import call_github_task
from projects.models import Project
from users.serializers import (
    UserIdsSerializer,
    UserListSerializer,
    UserPermissionGroupSummarySerializer,
)
from util.drf_writable_nested.serializers import (
    DeleteBeforeUpdateWritableNestedModelSerializer,
)

from .constants import INTERSECTION, UNION
from .feature_segments.limits import (
    SEGMENT_OVERRIDE_LIMIT_EXCEEDED_MESSAGE,
    exceeds_segment_override_limit,
)
from .feature_segments.serializers import (
    CustomCreateSegmentOverrideFeatureSegmentSerializer,
)
from .models import Feature, FeatureState
from .multivariate.serializers import NestedMultivariateFeatureOptionSerializer


class FeatureStateSerializerSmall(serializers.ModelSerializer):  # type: ignore[type-arg]
    feature_state_value = serializers.SerializerMethodField()

    class Meta:
        model = FeatureState
        fields = (
            "id",
            "feature_state_value",
            "environment",
            "identity",
            "feature_segment",
            "enabled",
        )

    def get_feature_state_value(self, obj):  # type: ignore[no-untyped-def]
        return obj.get_feature_state_value(identity=self.context.get("identity"))


class FeatureQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    search = serializers.CharField(required=False)
    sort_field = serializers.ChoiceField(
        choices=("created_date", "name"), default="created_date"
    )
    sort_direction = serializers.ChoiceField(choices=("ASC", "DESC"), default="ASC")

    tags = serializers.CharField(
        required=False,
        help_text=(
            "Comma separated list of tag ids to filter on (AND with "
            "INTERSECTION, and OR with UNION via tag_strategy)"
        ),
    )
    tag_strategy = serializers.ChoiceField(
        choices=(UNION, INTERSECTION), default=INTERSECTION
    )

    is_archived = serializers.BooleanField(required=False)
    environment = serializers.IntegerField(
        required=False,
        help_text="Integer ID of the environment to view features in the context of.",
    )
    is_enabled = serializers.BooleanField(
        allow_null=True,
        required=False,
        default=None,
        help_text="Boolean value to filter features as enabled or disabled.",
    )
    value_search = serializers.CharField(
        required=False,
        default=None,
        help_text="Value of type int, string, or boolean to filter features based on their values",
    )

    owners = serializers.CharField(
        required=False,
        help_text="Comma separated list of owner ids to filter on",
    )
    group_owners = serializers.CharField(
        required=False,
        help_text="Comma separated list of group owner ids to filter on",
    )

    def validate_owners(self, owners: str) -> list[int]:
        try:
            return [int(owner_id.strip()) for owner_id in owners.split(",")]
        except ValueError:
            raise serializers.ValidationError("Owner IDs must be integers.")

    def validate_group_owners(self, group_owners: str) -> list[int]:
        try:
            return [
                int(group_owner_id.strip())
                for group_owner_id in group_owners.split(",")
            ]
        except ValueError:
            raise serializers.ValidationError("Group owner IDs must be integers.")

    def validate_tags(self, tags: str) -> list[int]:
        try:
            return [int(tag_id.strip()) for tag_id in tags.split(",")]
        except ValueError:
            raise serializers.ValidationError("Tag IDs must be integers.")


class CreateFeatureSerializer(DeleteBeforeUpdateWritableNestedModelSerializer):
    multivariate_options = NestedMultivariateFeatureOptionSerializer(
        many=True, required=False
    )
    owners = UserListSerializer(many=True, read_only=True)
    group_owners = UserPermissionGroupSummarySerializer(many=True, read_only=True)

    environment_feature_state = serializers.SerializerMethodField()

    num_segment_overrides = serializers.SerializerMethodField(
        help_text="Number of segment overrides that exist for the given feature "
        "in the environment provided by the `environment` query parameter."
    )
    num_identity_overrides = serializers.SerializerMethodField(
        help_text="Number of identity overrides that exist for the given feature "
        "in the environment provided by the `environment` query parameter. "
        "Note: will return null for Edge enabled projects."
    )
    is_num_identity_overrides_complete = serializers.SerializerMethodField(
        help_text="A boolean that indicates whether there are more"
        " identity overrides than are being listed, if `False`. This field is "
        "`True` when querying overrides data for a features list page and "
        "exact data has been returned."
    )

    last_modified_in_any_environment = serializers.SerializerMethodField(
        help_text="Datetime representing the last time that the feature was modified "
        "in any environment in the given project. Note: requires feature "
        "versioning v2 enabled on the environment."
    )
    last_modified_in_current_environment = serializers.SerializerMethodField(
        help_text="Datetime representing the last time that the feature was modified "
        "in any environment in the current environment. Note: requires that "
        "the environment query parameter is passed and feature versioning v2 "
        "enabled on the environment."
    )

    class Meta:
        model = Feature
        fields = (
            "id",
            "name",
            "type",
            "default_enabled",
            "initial_value",
            "created_date",
            "description",
            "tags",
            "multivariate_options",
            "is_archived",
            "owners",
            "group_owners",
            "uuid",
            "project",
            "environment_feature_state",
            "num_segment_overrides",
            "num_identity_overrides",
            "is_num_identity_overrides_complete",
            "is_server_key_only",
            "last_modified_in_any_environment",
            "last_modified_in_current_environment",
        )
        read_only_fields = ("feature_segments", "created_date", "uuid", "project")

    def to_internal_value(self, data):  # type: ignore[no-untyped-def]
        if data.get("initial_value") and not isinstance(data["initial_value"], str):
            data["initial_value"] = str(data["initial_value"])
        return super(CreateFeatureSerializer, self).to_internal_value(data)

    def create(self, validated_data: dict) -> Feature:  # type: ignore[type-arg]
        project = self.context["project"]
        self.validate_project_features_limit(project)

        # Add the default(User creating the feature) owner of the feature
        # NOTE: pop the user before passing the data to create
        user = validated_data.pop("user", None)
        instance = super(CreateFeatureSerializer, self).create(validated_data)  # type: ignore[no-untyped-call]
        if user and getattr(user, "is_master_api_key_user", False) is False:
            instance.owners.add(user)
        return instance  # type: ignore[no-any-return]

    def validate_project_features_limit(self, project: Project) -> None:
        if project.features.count() >= project.max_features_allowed:
            raise serializers.ValidationError(
                {
                    "project": "The Project has reached the maximum allowed features limit."
                }
            )

    def validate_multivariate_options(self, multivariate_options):  # type: ignore[no-untyped-def]
        if multivariate_options:
            user = self.context["request"].user
            project = self.context.get("project")

            if user.is_authenticated and not (
                project and user.is_project_admin(project)
            ):
                raise PermissionDenied(
                    "User must be project admin to modify / create MV options."
                )
            total_percentage_allocation = sum(
                mv_option.get("default_percentage_allocation", 100)
                for mv_option in multivariate_options
            )
            if total_percentage_allocation > 100:
                raise serializers.ValidationError("Invalid percentage allocation")
        return multivariate_options

    def validate_name(self, name: str):  # type: ignore[no-untyped-def]
        view = self.context["view"]

        project = self.context["project"]
        feature_name_regex = project.feature_name_regex

        if not project.is_feature_name_valid(name):
            raise serializers.ValidationError(
                f"Feature name must match regex: {feature_name_regex}"
            )

        unique_filters = {
            "project__id": view.kwargs.get("project_pk"),
            "name__iexact": name,
        }
        existing_feature_queryset = Feature.objects.filter(**unique_filters)
        if self.instance:
            existing_feature_queryset = existing_feature_queryset.exclude(
                id=self.instance.id  # type: ignore[union-attr]
            )

        if existing_feature_queryset.exists():
            raise serializers.ValidationError(
                "Feature with that name already exists for this "
                "project. Note that feature names are case "
                "insensitive."
            )

        return name

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        view = self.context["view"]
        project_id = str(view.kwargs.get("project_pk"))
        if not project_id.isdigit():
            raise serializers.ValidationError("Invalid project ID.")

        # If tags selected check they from the same Project as Feature Project
        if any(tag.project_id != int(project_id) for tag in attrs.get("tags", [])):
            raise serializers.ValidationError(
                "Selected Tags must be from the same Project as current Feature"
            )

        return attrs

    @swagger_serializer_method(  # type: ignore[misc]
        serializer_or_field=FeatureStateSerializerSmall(allow_null=True)
    )
    def get_environment_feature_state(  # type: ignore[return]
        self, instance: Feature
    ) -> dict[str, typing.Any] | None:
        if (feature_states := self.context.get("feature_states")) and (
            feature_state := feature_states.get(instance.id)
        ):
            return FeatureStateSerializerSmall(instance=feature_state).data

    def get_num_segment_overrides(self, instance) -> int:  # type: ignore[no-untyped-def]
        try:
            return self.context["overrides_data"][instance.id].num_segment_overrides  # type: ignore[no-any-return]
        except (KeyError, AttributeError):
            return 0

    def get_num_identity_overrides(self, instance) -> typing.Optional[int]:  # type: ignore[no-untyped-def]
        try:
            return self.context["overrides_data"][instance.id].num_identity_overrides  # type: ignore[no-any-return]
        except (KeyError, AttributeError):
            return None

    def get_is_num_identity_overrides_complete(self, instance) -> typing.Optional[int]:  # type: ignore[no-untyped-def]  # noqa: E501
        try:
            return self.context["overrides_data"][  # type: ignore[no-any-return]
                instance.id
            ].is_num_identity_overrides_complete
        except (KeyError, AttributeError):
            return None

    def get_last_modified_in_any_environment(
        self, instance: Feature
    ) -> datetime | None:
        return getattr(instance, "last_modified_in_any_environment", None)

    def get_last_modified_in_current_environment(
        self, instance: Feature
    ) -> datetime | None:
        return getattr(instance, "last_modified_in_current_environment", None)


class FeatureSerializerWithMetadata(SerializerWithMetadata, CreateFeatureSerializer):
    metadata = MetadataSerializer(required=False, many=True)

    class Meta(CreateFeatureSerializer.Meta):
        fields = CreateFeatureSerializer.Meta.fields + ("metadata",)  # type: ignore[assignment]

    def get_project(
        self,
        validated_data: dict[str, typing.Any] | None = None,
    ) -> Project:
        project = self.context.get("project")
        if project:
            return project  # type: ignore[no-any-return]
        else:
            raise serializers.ValidationError(
                "Unable to retrieve project for metadata validation."
            )

    def update(
        self, instance: models.Model, validated_data: dict[str, typing.Any]
    ) -> Feature:
        metadata_items = validated_data.pop("metadata", [])
        feature = super().update(instance, validated_data)
        self.update_metadata(feature, metadata_items)
        feature.refresh_from_db()
        assert isinstance(feature, Feature)
        return feature


class UpdateFeatureSerializerWithMetadata(FeatureSerializerWithMetadata):
    """prevent users from changing certain values after creation"""

    class Meta(FeatureSerializerWithMetadata.Meta):
        read_only_fields = FeatureSerializerWithMetadata.Meta.read_only_fields + (  # type: ignore[assignment]
            "default_enabled",
            "initial_value",
            "name",
        )


class ListFeatureSerializer(FeatureSerializerWithMetadata):
    # This exists purely to reduce the conflicts for the EE repository
    # which has some extra behaviour here to support Oracle DB.
    pass


class UpdateFeatureSerializer(ListFeatureSerializer):
    """prevent users from changing certain values after creation"""

    class Meta(ListFeatureSerializer.Meta):
        read_only_fields = ListFeatureSerializer.Meta.read_only_fields + (  # type: ignore[assignment]
            "default_enabled",
            "initial_value",
            "name",
        )


class FeatureSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Feature
        fields = (
            "id",
            "name",
            "created_date",
            "description",
            "initial_value",
            "default_enabled",
            "type",
        )
        writeonly_fields = ("initial_value", "default_enabled")


class SDKFeatureSerializer(HideSensitiveFieldsSerializerMixin, FeatureSerializer):
    sensitive_fields = (
        "created_date",
        "description",
        "initial_value",
        "default_enabled",
    )


class FeatureStateSerializerFull(serializers.ModelSerializer):  # type: ignore[type-arg]
    feature = FeatureSerializer()
    feature_state_value = serializers.SerializerMethodField()

    class Meta:
        model = FeatureState
        fields = (
            "id",
            "feature",
            "feature_state_value",
            "environment",
            "identity",
            "feature_segment",
            "enabled",
        )

    def get_feature_state_value(self, obj):  # type: ignore[no-untyped-def]
        return obj.get_feature_state_value(identity=self.context.get("identity"))


class FeatureOwnerInputSerializer(UserIdsSerializer):
    def add_owners(self, feature: Feature):  # type: ignore[no-untyped-def]
        user_ids = self.validated_data["user_ids"]
        feature.owners.add(*user_ids)

    def remove_users(self, feature: Feature):  # type: ignore[no-untyped-def]
        user_ids = self.validated_data["user_ids"]
        feature.owners.remove(*user_ids)


class FeatureGroupOwnerInputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    group_ids = serializers.ListField(child=serializers.IntegerField())

    def add_group_owners(self, feature: Feature):  # type: ignore[no-untyped-def]
        group_ids = self.validated_data["group_ids"]
        feature.group_owners.add(*group_ids)

    def remove_group_owners(self, feature: Feature):  # type: ignore[no-untyped-def]
        group_ids = self.validated_data["group_ids"]
        feature.group_owners.remove(*group_ids)


class ProjectFeatureSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    owners = UserListSerializer(many=True, read_only=True)
    group_owners = UserPermissionGroupSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Feature
        fields = (
            "id",
            "name",
            "created_date",
            "description",
            "initial_value",
            "default_enabled",
            "type",
            "owners",
            "group_owners",
            "is_server_key_only",
        )
        writeonly_fields = ("initial_value", "default_enabled")


class SDKFeatureStateSerializer(
    HideSensitiveFieldsSerializerMixin, FeatureStateSerializerFull
):
    feature = SDKFeatureSerializer()
    sensitive_fields = (
        "id",
        "environment",
        "identity",
        "feature_segment",
    )


class FeatureStateSerializerBasic(WritableNestedModelSerializer):
    feature_state_value = serializers.SerializerMethodField()
    multivariate_feature_state_values = MultivariateFeatureStateValueSerializer(
        many=True, required=False
    )
    identifier = serializers.CharField(
        required=False,
        help_text="Can be passed as an alternative to `identity`",
    )

    class Meta:
        model = FeatureState
        fields = "__all__"
        read_only_fields = ("version", "created_at", "updated_at", "status")

    def get_feature_state_value(self, obj):  # type: ignore[no-untyped-def]
        return obj.get_feature_state_value(identity=self.context.get("identity"))

    def save(self, **kwargs):  # type: ignore[no-untyped-def]
        try:
            response = super().save(**kwargs)  # type: ignore[no-untyped-call]

            feature_state = self.instance
            if (
                not feature_state.identity_id  # type: ignore[union-attr]
                and feature_state.feature.external_resources.exists()  # type: ignore[union-attr]
                and feature_state.environment.project.github_project.exists()  # type: ignore[union-attr]
                and feature_state.environment.project.organisation.github_config.exists()  # type: ignore[union-attr]
            ):
                call_github_task(
                    organisation_id=feature_state.feature.project.organisation_id,  # type: ignore[union-attr]
                    type=GitHubEventType.FLAG_UPDATED.value,
                    feature=feature_state.feature,  # type: ignore[union-attr]
                    segment_name=None,
                    url=None,
                    feature_states=[feature_state],
                )

            return response

        except django.core.exceptions.ValidationError as e:
            raise serializers.ValidationError(str(e))

    def validate_feature(self, feature):  # type: ignore[no-untyped-def]
        if self.instance and self.instance.feature_id != feature.id:  # type: ignore[union-attr]
            raise serializers.ValidationError(
                "Cannot change the feature of a feature state"
            )
        return feature

    def validate_environment(self, environment):  # type: ignore[no-untyped-def]
        if self.instance and self.instance.environment_id != environment.id:  # type: ignore[union-attr]
            raise serializers.ValidationError(
                "Cannot change the environment of a feature state"
            )
        return environment

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        environment = attrs.get("environment") or self.context["environment"]
        identity = attrs.get("identity")
        feature_segment = attrs.get("feature_segment")
        identifier = attrs.pop("identifier", None)
        feature = attrs.get("feature")
        if feature and feature.project_id != environment.project_id:
            error = {"feature": "Feature does not exist in project"}
            raise serializers.ValidationError(error)

        if identifier:
            try:
                identity = Identity.objects.get(
                    identifier=identifier, environment=environment
                )
                attrs["identity"] = identity
            except Identity.DoesNotExist:
                raise serializers.ValidationError("Invalid identifier")

        if identity and not identity.environment == environment:
            raise serializers.ValidationError("Identity does not exist in environment.")

        if feature_segment and not feature_segment.environment == environment:
            raise serializers.ValidationError(
                "Feature Segment does not belong to environment."
            )

        mv_values = attrs.get("multivariate_feature_state_values", [])
        if sum([v["percentage_allocation"] for v in mv_values]) > 100:
            raise serializers.ValidationError(
                "Multivariate percentage values exceed 100%."
            )

        return attrs


class FeatureStateSerializerWithIdentity(FeatureStateSerializerBasic):
    class _IdentitySerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
        class Meta:
            model = Identity
            fields = ("id", "identifier")

    identity = _IdentitySerializer()


class FeatureStateSerializerCreate(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = FeatureState
        fields = ("feature", "enabled")


class FeatureInfluxDataSerializer(serializers.Serializer):  # type: ignore[type-arg]
    events_list = serializers.ListSerializer(child=serializers.DictField())  # type: ignore[var-annotated]


class FeatureEvaluationDataSerializer(serializers.Serializer):  # type: ignore[type-arg]
    day = serializers.CharField()
    count = serializers.IntegerField()


class GetInfluxDataQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    period = serializers.CharField(required=False, default="24h")
    environment_id = serializers.CharField(required=True)
    aggregate_every = serializers.CharField(required=False, default="24h")


class GetUsageDataQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    period = serializers.IntegerField(
        required=False, default=30, help_text="number of days"
    )
    environment_id = serializers.IntegerField(required=True)


class WritableNestedFeatureStateSerializer(FeatureStateSerializerBasic):
    feature_state_value = FeatureStateValueSerializer(required=False)  # type: ignore[assignment]

    class Meta(FeatureStateSerializerBasic.Meta):
        extra_kwargs = {"environment": {"required": True}}


class SegmentAssociatedFeatureStateSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = FeatureState
        fields = ("id", "feature", "environment")


class AssociatedFeaturesQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    environment = serializers.IntegerField(required=False)


class SDKFeatureStatesQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    feature = serializers.CharField(
        required=False, help_text="Name of the feature to get the state of"
    )


class CustomCreateSegmentOverrideFeatureStateSerializer(
    CreateSegmentOverrideFeatureStateSerializer
):
    validate_override_limit = True

    feature_segment = CustomCreateSegmentOverrideFeatureSegmentSerializer(
        required=False, allow_null=True
    )

    def _get_save_kwargs(self, field_name):  # type: ignore[no-untyped-def]
        kwargs = super()._get_save_kwargs(field_name)  # type: ignore[no-untyped-call]
        if field_name == "feature_segment":
            kwargs["feature"] = self.context.get("feature")
            kwargs["environment"] = self.context.get("environment")
            kwargs["environment_feature_version"] = self.context.get(
                "environment_feature_version"
            )
        return kwargs

    def create(self, validated_data: dict) -> FeatureState:  # type: ignore[type-arg]
        environment = validated_data["environment"]
        if self.validate_override_limit and exceeds_segment_override_limit(environment):
            raise serializers.ValidationError(
                {"environment": SEGMENT_OVERRIDE_LIMIT_EXCEEDED_MESSAGE}
            )
        return super().create(validated_data)  # type: ignore[no-any-return,no-untyped-call]
