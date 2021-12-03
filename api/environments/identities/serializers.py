from flag_engine.identities.builders import build_identity_dict
from flag_engine.identities.models import IdentityModel as EngineIdentity
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from environments.identities.models import Identity
from environments.serializers import EnvironmentSerializerFull
from features.models import FeatureState
from features.serializers import (
    FeatureStateSerializerFull,
    FeatureStateValueSerializer,
    MultivariateFeatureStateValueSerializer,
)


class IdentifierOnlyIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        fields = ("identifier",)


class IdentitySerializerFull(serializers.ModelSerializer):
    identity_features = FeatureStateSerializerFull(many=True)
    environment = EnvironmentSerializerFull()

    class Meta:
        model = Identity
        fields = ("id", "identifier", "identity_features", "environment")


class EdgeIdentitySerializer(serializers.ModelSerializer):
    identity_uuid = serializers.CharField(required=False)

    class Meta:
        model = Identity
        fields = ("identifier", "environment", "identity_uuid")
        read_only_fields = ("environment", "identity_uuid")

    def save(self, **kwargs):
        identifier = self.validated_data.get("identifier")
        environment_api_key = self.context["view"].kwargs["environment_api_key"]
        self.instance = EngineIdentity(
            identifier=identifier, environment_api_key=environment_api_key
        )
        Identity.put_item_dynamodb(build_identity_dict(self.instance))
        return self.instance


class EdgeIdentitySerializerFeatureStateSerializer(EdgeIdentitySerializer):
    feature_state_value = FeatureStateValueSerializer(required=False)
    multivariate_feature_state_values = MultivariateFeatureStateValueSerializer(
        many=True, required=False
    )

    class Meta:
        model = FeatureState
        fields = (
            "feature",
            "environment",
            "feature_state_value",
            "multivariate_feature_state_values",
        )


class IdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        fields = ("id", "identifier", "environment")
        read_only_fields = ("id", "environment")

    def save(self, **kwargs):
        environment = kwargs.get("environment")
        identifier = self.validated_data.get("identifier")

        if Identity.objects.filter(
            environment=environment, identifier=identifier
        ).exists():
            raise ValidationError(
                {
                    "identifier": "Identity with identifier '%s' already exists in this environment"
                    % identifier
                }
            )
        return super(IdentitySerializer, self).save(**kwargs)
