import typing
from collections import defaultdict

from core.constants import BOOLEAN, FLOAT, INTEGER, STRING
from rest_framework import serializers

from environments.identities.models import Identity
from environments.identities.serializers import (
    IdentifierOnlyIdentitySerializer,
)
from environments.identities.traits.fields import TraitValueField
from environments.identities.traits.models import Trait
from environments.identities.traits.serializers import TraitSerializerBasic
from features.serializers import (
    FeatureStateSerializerFull,
    SDKFeatureStateSerializer,
)
from integrations.integration import identify_integrations
from segments.serializers import SegmentSerializerBasic

from .serializers_mixins import HideSensitiveFieldsSerializerMixin


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
            "value_type": (
                trait_value_type
                if trait_value_type in [FLOAT, INTEGER, BOOLEAN]
                else STRING
            ),
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

    class Meta(SDKCreateUpdateTraitSerializer.Meta):
        class BulkTraitListSerializer(serializers.ListSerializer):
            """
            Create a custom ListSerializer that is only used by this serializer to
            optimise the way in which we create, update and delete traits in the db
            """

            def update(self, instance, validated_data):
                return self.save()

            def save(self, **kwargs):
                identity_trait_items = self._build_identifier_trait_items_dictionary()
                modified_traits = []
                for identifier, trait_data_items in identity_trait_items.items():
                    identity, _ = Identity.objects.get_or_create(
                        identifier=identifier,
                        environment=self.context["request"].environment,
                    )
                    modified_traits.extend(identity.update_traits(trait_data_items))
                return modified_traits

            def _build_identifier_trait_items_dictionary(
                self,
            ) -> typing.Dict[str, typing.List[typing.Dict]]:
                """
                build a dictionary of the form
                {"identifier": [{"trait_key": "key", "trait_value": "value"}, ...]}
                """
                identity_trait_items = defaultdict(list)
                for item in self.validated_data:
                    # item will be in the format:
                    # {"identity": {"identifier": "foo"}, "trait_key": "foo", "trait_value": "bar"}
                    identity_trait_items[item["identity"]["identifier"]].append(
                        dict((k, v) for k, v in item.items() if k != "identity")
                    )
                return identity_trait_items

        list_serializer_class = BulkTraitListSerializer


class IdentitySerializerWithTraitsAndSegments(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    flags = FeatureStateSerializerFull(many=True)
    traits = TraitSerializerBasic(many=True)
    segments = SegmentSerializerBasic(many=True)


class IdentifyWithTraitsSerializer(
    HideSensitiveFieldsSerializerMixin, serializers.Serializer
):
    identifier = serializers.CharField(write_only=True, required=True)
    traits = TraitSerializerBasic(required=False, many=True)
    flags = SDKFeatureStateSerializer(read_only=True, many=True)

    sensitive_fields = ("traits",)

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

        all_feature_states = identity.get_all_feature_states(
            traits=trait_models,
            additional_filters=self.context.get("feature_states_additional_filters"),
        )
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
