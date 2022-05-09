from flag_engine.features.models import (
    FeatureStateModel as EngineFeatureStateModel,
)
from flag_engine.features.models import (
    MultivariateFeatureStateValueModel as EngineMultivariateFeatureStateValueModel,
)
from flag_engine.features.schemas import MultivariateFeatureStateValueSchema
from flag_engine.identities.builders import build_identity_dict
from flag_engine.identities.models import IdentityModel as EngineIdentity
from flag_engine.utils.exceptions import (
    DuplicateFeatureState,
    InvalidPercentageAllocation,
)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from environments.identities.models import Identity
from features.models import Feature, FeatureState, FeatureStateValue
from features.multivariate.models import MultivariateFeatureOption
from features.serializers import FeatureStateValueSerializer

engine_multi_fs_value_schema = MultivariateFeatureStateValueSchema()


class EdgeIdentitySerializer(serializers.Serializer):
    identity_uuid = serializers.CharField(read_only=True)
    identifier = serializers.CharField(required=True, max_length=2000)

    def save(self, **kwargs):
        identifier = self.validated_data.get("identifier")
        environment_api_key = self.context["view"].kwargs["environment_api_key"]
        self.instance = EngineIdentity(
            identifier=identifier, environment_api_key=environment_api_key
        )
        if Identity.dynamo_wrapper.get_item(self.instance.composite_key):
            raise ValidationError(
                f"Identity with identifier: {identifier} already exists"
            )
        Identity.dynamo_wrapper.put_item(build_identity_dict(self.instance))
        return self.instance


class EdgeMultivariateFeatureOptionField(serializers.IntegerField):
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return MultivariateFeatureOption.objects.get(id=data)

    def to_representation(self, obj):
        return obj.id


class EdgeMultivariateFeatureStateValueSerializer(serializers.Serializer):
    multivariate_feature_option = EdgeMultivariateFeatureOptionField()
    percentage_allocation = serializers.FloatField(max_value=100, min_value=0)

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return EngineMultivariateFeatureStateValueModel(**data)


class FeatureStateValueEdgeIdentityField(serializers.Field):
    def to_representation(self, obj):
        identity_id = self.parent.get_identity_uuid()
        return obj.get_value(identity_id=identity_id)

    def get_attribute(self, instance):
        # We pass the object instance onto `to_representation`,
        # not just the field attribute.
        return instance

    def to_internal_value(self, data):
        fsv_type = FeatureState.get_feature_state_value_type(data)
        feature_state_value_dict = {
            "type": fsv_type,
            FeatureState.get_feature_state_key_name(fsv_type): data,
        }
        fs_value_serializer = FeatureStateValueSerializer(data=feature_state_value_dict)
        fs_value_serializer.is_valid(raise_exception=True)
        return FeatureStateValue(**feature_state_value_dict).value


class EdgeFeatureField(serializers.IntegerField):
    def to_representation(self, obj):
        return obj.id

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        feature = Feature.objects.get(id=data)
        return feature


class EdgeIdentityFeatureStateSerializer(serializers.Serializer):
    feature_state_value = FeatureStateValueEdgeIdentityField(allow_null=True)
    feature = EdgeFeatureField()
    multivariate_feature_state_values = EdgeMultivariateFeatureStateValueSerializer(
        many=True, required=False
    )
    enabled = serializers.BooleanField(required=False, default=False)
    identity_uuid = serializers.SerializerMethodField()

    featurestate_uuid = serializers.CharField(required=False, read_only=True)

    def get_identity_uuid(self, obj=None):
        return self.context["view"].kwargs["edge_identity_identity_uuid"]

    def save(self, **kwargs):
        identity = self.context["view"].identity
        feature_state_value = self.validated_data.pop("feature_state_value")
        if not self.instance:
            self.instance = EngineFeatureStateModel(**self.validated_data)
            try:
                identity.identity_features.append(self.instance)
            except DuplicateFeatureState as e:
                raise serializers.ValidationError(
                    "Feature state already exists."
                ) from e
        self.instance.set_value(feature_state_value)
        self.instance.enabled = self.validated_data["enabled"]
        self.instance.multivariate_feature_state_values = self.validated_data[
            "multivariate_feature_state_values"
        ]

        try:
            identity_dict = build_identity_dict(identity)
        except InvalidPercentageAllocation as e:
            raise serializers.ValidationError(
                {
                    "multivariate_feature_state_values": "Total percentage allocation "
                    "for feature must be less than 100 percent"
                }
            ) from e

        Identity.dynamo_wrapper.put_item(identity_dict)
        return self.instance


class EdgeIdentityTraitsSerializer(serializers.Serializer):
    trait_key = serializers.CharField()
    trait_value = serializers.CharField(allow_null=True)


class EdgeIdentityFsQueryparamSerializer(serializers.Serializer):
    feature = serializers.IntegerField(
        required=False, help_text="ID of the feature to filter by"
    )
