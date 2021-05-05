from rest_framework import serializers

from environments.identities.models import Identity
from environments.identities.serializers import (
    IdentifierOnlyIdentitySerializer,
)
from environments.identities.traits.fields import TraitValueField
from environments.identities.traits.models import Trait
from environments.identities.traits.serializers import TraitSerializerBasic
from environments.models import BOOLEAN, FLOAT, INTEGER, STRING
from features.serializers import FeatureStateSerializerFull
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

    def create(self, validated_data):
        """
        Create the identity with the associated traits
        (optionally store traits if flag set on org)
        """
        environment = self.context["environment"]
        identity, created = Identity.objects.get_or_create(
            identifier=validated_data["identifier"], environment=environment
        )

        if not created and environment.project.organisation.persist_trait_data:
            # if this is an update and we're persisting traits, then we need to
            # partially update any traits and return the full list
            return self.update(instance=identity, validated_data=validated_data)

        # generate traits for the identity and store them if configured to do so
        trait_models = identity.generate_traits(
            validated_data.get("traits", []),
            persist=environment.project.organisation.persist_trait_data,
        )

        return {
            "identity": identity,
            "traits": trait_models,
            "flags": identity.get_all_feature_states(traits=trait_models),
        }

    def update(self, instance, validated_data):
        """partially update any traits and return the full list of traits and flags"""
        trait_data_items = validated_data.get("traits", [])
        updated_traits = instance.update_traits(trait_data_items)

        return {
            "identity": instance,
            "traits": updated_traits,
            "flags": instance.get_all_feature_states(traits=updated_traits),
        }
