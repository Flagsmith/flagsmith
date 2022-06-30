import typing

from core.constants import BOOLEAN, FLOAT, INTEGER, STRING
from rest_framework import serializers

from environments.identities.models import Identity
from environments.identities.serializers import (
    IdentifierOnlyIdentitySerializer,
)
from environments.identities.traits.fields import TraitValueField
from environments.identities.traits.models import Trait
from environments.identities.traits.serializers import TraitSerializerBasic
from features.serializers import FeatureStateSerializerFull
from integrations.integration import identify_integrations
from segments.serializers import SegmentSerializerBasic


class SDKCreateUpdateTraitSerializer(serializers.ModelSerializer):
    identity = IdentifierOnlyIdentitySerializer()
    trait_value = TraitValueField()
    trait_key = serializers.CharField()

    class Meta:
        model = Trait
        fields = ("identity", "trait_value", "trait_key")

    def create(self, validated_data):
        identity = self._get_identity(validated_data["identity"]["identifier"])

        trait_key = validated_data["trait_key"]
        trait_value = validated_data["trait_value"]["value"]
        trait_value_type = validated_data["trait_value"]["type"]

        value_key = Trait.get_trait_value_key_name(trait_value_type)

        defaults = {
            value_key: trait_value,
            "value_type": trait_value_type
            if trait_value_type in [FLOAT, INTEGER, BOOLEAN]
            else STRING,
        }

        return Trait.objects.update_or_create(
            identity=identity, trait_key=trait_key, defaults=defaults
        )[0]

    def validate(self, attrs):
        request = self.context["request"]
        if not request.environment.trait_persistence_allowed(request):
            raise serializers.ValidationError(
                "Setting traits not allowed with client key."
            )
        return attrs

    def _get_identity(self, identifier):
        return Identity.objects.get_or_create(
            identifier=identifier, environment=self.context["environment"]
        )[0]


class SDKBulkCreateUpdateTraitSerializer(SDKCreateUpdateTraitSerializer):
    trait_value = TraitValueField(allow_null=True)


class IdentitySerializerWithTraitsAndSegments(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    flags = FeatureStateSerializerFull(many=True)
    traits = TraitSerializerBasic(many=True)
    segments = SegmentSerializerBasic(many=True)


class IdentifyWithTraitsSerializer(serializers.Serializer):
    identifier = serializers.CharField(write_only=True, required=True)
    traits = TraitSerializerBasic(required=False, many=True)
    flags = FeatureStateSerializerFull(read_only=True, many=True)

    def save(self, **kwargs):
        """
        Create the identity with the associated traits
        (optionally store traits if flag set on org)
        """
        environment = self.context["environment"]
        identity, created = Identity.objects.get_or_create(
            identifier=self.validated_data["identifier"], environment=environment
        )

        trait_data_items = self.validated_data.get("traits", [])

        if not created and environment.project.organisation.persist_trait_data:
            # if this is an update and we're persisting traits, then we need to
            # partially update any traits and return the full list
            trait_models = identity.update_traits(trait_data_items)
        else:
            # generate traits for the identity and store them if configured to do so
            trait_models = identity.generate_traits(
                trait_data_items,
                persist=environment.project.organisation.persist_trait_data,
            )

        all_feature_states = identity.get_all_feature_states(traits=trait_models)
        identify_integrations(identity, all_feature_states, trait_models)

        return {
            "identity": identity,
            "traits": trait_models,
            "flags": all_feature_states,
        }

    def validate_traits(self, traits: typing.List[dict] = None):
        request = self.context["request"]
        if traits and not request.environment.trait_persistence_allowed(request):
            raise serializers.ValidationError(
                "Setting traits not allowed with client key."
            )
        return traits
