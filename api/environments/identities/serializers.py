from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from environments.identities.models import Identity
from environments.serializers import EnvironmentSerializerFull
from features.serializers import FeatureStateSerializerFull


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


class SDKIdentitiesResponseSerializer(serializers.Serializer):
    class _TraitSerializer(serializers.Serializer):
        trait_key = serializers.CharField()
        trait_value = serializers.Field(
            help_text="Can be of type string, boolean, float or integer."
        )

    flags = serializers.ListField(child=FeatureStateSerializerFull())
    traits = serializers.ListSerializer(child=_TraitSerializer())


class SDKIdentitiesQuerySerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
