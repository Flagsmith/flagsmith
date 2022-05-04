import django.core.exceptions
from rest_framework import serializers

from audit.models import (
    FEATURE_STATE_UPDATED_MESSAGE,
    IDENTITY_FEATURE_STATE_UPDATED_MESSAGE,
    AuditLog,
    RelatedObjectType,
)
from environments.identities.models import Identity
from users.serializers import UserIdsSerializer, UserListSerializer
from util.drf_writable_nested.serializers import WritableNestedModelSerializer

from .models import Feature, FeatureState, FeatureStateValue
from .multivariate.serializers import (
    MultivariateFeatureOptionSerializer,
    MultivariateFeatureStateValueSerializer,
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


class ListCreateFeatureSerializer(WritableNestedModelSerializer):
    multivariate_options = MultivariateFeatureOptionSerializer(
        many=True, read_only=True
    )
    owners = UserListSerializer(many=True, read_only=True)

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
        )
        read_only_fields = ("feature_segments", "created_date")

    def to_internal_value(self, data):
        if data.get("initial_value") and not isinstance(data["initial_value"], str):
            data["initial_value"] = str(data["initial_value"])
        return super(ListCreateFeatureSerializer, self).to_internal_value(data)

    def create(self, validated_data):
        # Add the default(User creating the feature) owner of the feature
        # NOTE: pop the user before passing the data to create
        user = validated_data.pop("user")
        instance = super(ListCreateFeatureSerializer, self).create(validated_data)
        instance.owners.add(user)
        return instance

    def validate(self, attrs):
        view = self.context["view"]
        project_id = str(view.kwargs.get("project_pk"))
        if not project_id.isdigit():
            raise serializers.ValidationError("Invalid project ID.")
        unique_filters = {"project__id": project_id, "name__iexact": attrs["name"]}
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

        # If tags selected check they from the same Project as Feature Project
        if any(tag.project_id != int(project_id) for tag in attrs.get("tags", [])):
            raise serializers.ValidationError(
                "Selected Tags must be from the same Project as current Feature"
            )

        return attrs


class UpdateFeatureSerializer(ListCreateFeatureSerializer):
    """prevent users from changing the value of default enabled after creation"""

    class Meta(ListCreateFeatureSerializer.Meta):
        read_only_fields = ListCreateFeatureSerializer.Meta.read_only_fields + (
            "default_enabled",
            "initial_value",
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

    def create(self, validated_data):
        instance = super(FeatureStateSerializerBasic, self).create(validated_data)
        self._create_audit_log(instance=instance)
        return instance

    def update(self, instance, validated_data):
        updated_instance = super(FeatureStateSerializerBasic, self).update(
            instance, validated_data
        )
        self._create_audit_log(updated_instance)
        return updated_instance

    def _create_audit_log(self, instance):
        create_feature_state_audit_log(instance, self.context.get("request"))

    def validate(self, attrs):
        environment = attrs.get("environment")
        identity = attrs.get("identity")
        feature_segment = attrs.get("feature_segment")

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

    def save(self, **kwargs):
        instance = super(FeatureStateSerializerCreate, self).save(**kwargs)
        self._create_audit_log(instance=instance)
        return instance

    def _create_audit_log(self, instance):
        create_feature_state_audit_log(instance, self.context.get("request"))

    def validate(self, attrs):
        return super(FeatureStateSerializerCreate, self).validate(attrs)


def create_feature_state_audit_log(feature_state, request):
    if feature_state.identity:
        message = IDENTITY_FEATURE_STATE_UPDATED_MESSAGE % (
            feature_state.feature.name,
            feature_state.identity.identifier,
        )
    else:
        message = FEATURE_STATE_UPDATED_MESSAGE % feature_state.feature.name

    AuditLog.objects.create(
        author=getattr(request, "user", None),
        related_object_id=feature_state.id,
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        environment=feature_state.environment,
        project=feature_state.environment.project,
        log=message,
    )


class FeatureStateValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureStateValue
        fields = ("type", "string_value", "integer_value", "boolean_value")


class FeatureInfluxDataSerializer(serializers.Serializer):
    events_list = serializers.ListSerializer(child=serializers.DictField())


class GetInfluxDataQuerySerializer(serializers.Serializer):
    period = serializers.CharField(required=False, default="24h")
    environment_id = serializers.CharField(required=True)


class WritableNestedFeatureStateSerializer(FeatureStateSerializerBasic):
    feature_state_value = FeatureStateValueSerializer(required=False)

    class Meta(FeatureStateSerializerBasic.Meta):
        extra_kwargs = {"environment": {"required": True}}
