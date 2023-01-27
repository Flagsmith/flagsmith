import typing

import django.core.exceptions
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from environments.identities.models import Identity
from users.serializers import UserIdsSerializer, UserListSerializer
from util.drf_writable_nested.serializers import (
    DeleteBeforeUpdateWritableNestedModelSerializer,
)

from .models import Feature, FeatureState, FeatureStateValue
from .multivariate.serializers import (
    MultivariateFeatureStateValueSerializer,
    NestedMultivariateFeatureOptionSerializer,
)


class FeatureOwnerInputSerializer(UserIdsSerializer):
    def add_owners(self, feature: Feature):
        user_ids = self.validated_data["user_ids"]
        feature.owners.add(*user_ids)

    def remove_users(self, feature: Feature):
        user_ids = self.validated_data["user_ids"]
        feature.owners.remove(*user_ids)


class ProjectFeatureSerializer(serializers.ModelSerializer):
    owners = UserListSerializer(many=True, read_only=True)

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
        )
        writeonly_fields = ("initial_value", "default_enabled")


class FeatureQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False)
    sort_field = serializers.ChoiceField(
        choices=("created_date", "name"), default="created_date"
    )
    sort_direction = serializers.ChoiceField(choices=("ASC", "DESC"), default="ASC")

    tags = serializers.CharField(
        required=False, help_text="Comma separated list of tag ids to filter on (AND)"
    )
    is_archived = serializers.BooleanField(required=False)
    environment = serializers.IntegerField(
        required=False,
        help_text="Integer ID of the environment to view features in the context of.",
    )

    def validate_tags(self, tags):
        try:
            return [int(tag_id.strip()) for tag_id in tags.split(",")]
        except ValueError:
            raise serializers.ValidationError("Tag IDs must be integers.")


class ListCreateFeatureSerializer(DeleteBeforeUpdateWritableNestedModelSerializer):
    multivariate_options = NestedMultivariateFeatureOptionSerializer(
        many=True, required=False
    )
    owners = UserListSerializer(many=True, read_only=True)

    num_segment_overrides = serializers.SerializerMethodField(
        help_text="Number of segment overrides that exist for the given feature "
        "in the environment provided by the `environment` query parameter."
    )
    num_identity_overrides = serializers.SerializerMethodField(
        help_text="Number of identity overrides that exist for the given feature "
        "in the environment provided by the `environment` query parameter. "
        "Note: will return null for Edge enabled projects."
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
            "uuid",
            "project",
            "num_segment_overrides",
            "num_identity_overrides",
        )
        read_only_fields = ("feature_segments", "created_date", "uuid", "project")

    def to_internal_value(self, data):
        if data.get("initial_value") and not isinstance(data["initial_value"], str):
            data["initial_value"] = str(data["initial_value"])
        return super(ListCreateFeatureSerializer, self).to_internal_value(data)

    def create(self, validated_data):
        # Add the default(User creating the feature) owner of the feature
        # NOTE: pop the user before passing the data to create
        user = validated_data.pop("user", None)
        instance = super(ListCreateFeatureSerializer, self).create(validated_data)
        if user and not user.is_anonymous:
            instance.owners.add(user)
        return instance

    def validate_multivariate_options(self, multivariate_options):
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

    def validate_name(self, name: str):
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
                id=self.instance.id
            )

        if existing_feature_queryset.exists():
            raise serializers.ValidationError(
                "Feature with that name already exists for this "
                "project. Note that feature names are case "
                "insensitive."
            )

        return name

    def validate(self, attrs):
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

    def get_num_segment_overrides(self, instance) -> int:
        try:
            return self.context["overrides_data"][instance.id].num_segment_overrides
        except (KeyError, AttributeError):
            return 0

    def get_num_identity_overrides(self, instance) -> typing.Optional[int]:
        try:
            return self.context["overrides_data"][instance.id].num_identity_overrides
        except (KeyError, AttributeError):
            return None


class UpdateFeatureSerializer(ListCreateFeatureSerializer):
    """prevent users from changing certain values after creation"""

    class Meta(ListCreateFeatureSerializer.Meta):
        read_only_fields = ListCreateFeatureSerializer.Meta.read_only_fields + (
            "default_enabled",
            "initial_value",
            "name",
        )


class FeatureSerializer(serializers.ModelSerializer):
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


class FeatureStateSerializerFull(serializers.ModelSerializer):
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

    def get_feature_state_value(self, obj):
        return obj.get_feature_state_value(identity=self.context.get("identity"))


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

    def get_feature_state_value(self, obj):
        return obj.get_feature_state_value(identity=self.context.get("identity"))

    def save(self, **kwargs):
        try:
            return super().save(**kwargs)
        except django.core.exceptions.ValidationError as e:
            raise serializers.ValidationError(e.message)

    def validate(self, attrs):
        environment = attrs.get("environment")
        identity = attrs.get("identity")
        feature_segment = attrs.get("feature_segment")
        identifier = attrs.pop("identifier", None)
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
    class _IdentitySerializer(serializers.ModelSerializer):
        class Meta:
            model = Identity
            fields = ("id", "identifier")

    identity = _IdentitySerializer()


class FeatureStateSerializerCreate(serializers.ModelSerializer):
    class Meta:
        model = FeatureState
        fields = ("feature", "enabled")


class FeatureStateValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureStateValue
        fields = ("type", "string_value", "integer_value", "boolean_value")


class FeatureInfluxDataSerializer(serializers.Serializer):
    events_list = serializers.ListSerializer(child=serializers.DictField())


class FeatureUsageDataSerializer(serializers.Serializer):
    day = serializers.CharField()
    count = serializers.IntegerField()


class GetInfluxDataQuerySerializer(serializers.Serializer):
    period = serializers.CharField(required=False, default="24h")
    environment_id = serializers.CharField(required=True)
    aggregate_every = serializers.CharField(required=False, default="24h")


class GetUsageDataQuerySerializer(serializers.Serializer):
    period = serializers.CharField(
        required=False, default="1", help_text="number of days"
    )
    environment_id = serializers.CharField(required=True)


class WritableNestedFeatureStateSerializer(FeatureStateSerializerBasic):
    feature_state_value = FeatureStateValueSerializer(required=False)

    class Meta(FeatureStateSerializerBasic.Meta):
        extra_kwargs = {"environment": {"required": True}}


class SegmentAssociatedFeatureStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureState
        fields = ("id", "feature", "environment")


class SDKFeatureStatesQuerySerializer(serializers.Serializer):
    feature = serializers.CharField(
        required=False, help_text="Name of the feature to get the state of"
    )
