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
from environments.sdk.services import (
    get_identified_transient_identity_and_traits,
    get_persisted_identity_and_traits,
    get_transient_identity_and_traits,
)
from environments.sdk.types import SDKTraitData
from features.serializers import (
    FeatureStateSerializerFull,
    SDKFeatureStateSerializer,
)
from integrations.integration import identify_integrations
from segments.serializers import SegmentSerializerBasic

from .serializers_mixins import HideSensitiveFieldsSerializerMixin


class SDKCreateUpdateTraitSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    identity = IdentifierOnlyIdentitySerializer()
    trait_value = TraitValueField()
    trait_key = serializers.CharField()

    class Meta:
        model = Trait
        fields = ("identity", "trait_value", "trait_key")

    def create(self, validated_data):  # type: ignore[no-untyped-def]
        identity = self._get_identity(validated_data["identity"]["identifier"])  # type: ignore[no-untyped-call]

        trait_key = validated_data["trait_key"]
        trait_value = validated_data["trait_value"]["value"]
        trait_value_type = validated_data["trait_value"]["type"]

        value_key = Trait.get_trait_value_key_name(trait_value_type)  # type: ignore[no-untyped-call]

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

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        request = self.context["request"]
        if not request.environment.trait_persistence_allowed(request):
            raise serializers.ValidationError(
                "Setting traits not allowed with client key."
            )
        return attrs

    def _get_identity(self, identifier):  # type: ignore[no-untyped-def]
        return Identity.objects.get_or_create(
            identifier=identifier, environment=self.context["environment"]
        )[0]


class SDKBulkCreateUpdateTraitSerializer(SDKCreateUpdateTraitSerializer):
    trait_value = TraitValueField(allow_null=True)

    class Meta(SDKCreateUpdateTraitSerializer.Meta):
        class BulkTraitListSerializer(serializers.ListSerializer):  # type: ignore[type-arg]
            """
            Create a custom ListSerializer that is only used by this serializer to
            optimise the way in which we create, update and delete traits in the db
            """

            def update(self, instance, validated_data):  # type: ignore[no-untyped-def]
                return self.save()  # type: ignore[no-untyped-call]

            def save(self, **kwargs):  # type: ignore[no-untyped-def]
                identity_trait_items = self._build_identifier_trait_items_dictionary()
                modified_traits = []
                for identifier, trait_data_items in identity_trait_items.items():
                    identity, _ = Identity.objects.get_or_create(
                        identifier=identifier,
                        environment=self.context["request"].environment,
                    )
                    modified_traits.extend(identity.update_traits(trait_data_items))  # type: ignore[arg-type]
                return modified_traits

            def _build_identifier_trait_items_dictionary(
                self,
            ) -> typing.Dict[str, typing.List[typing.Dict]]:  # type: ignore[type-arg]
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


class IdentitySerializerWithTraitsAndSegments(serializers.Serializer):  # type: ignore[type-arg]
    def update(self, instance, validated_data):  # type: ignore[no-untyped-def]
        pass

    def create(self, validated_data):  # type: ignore[no-untyped-def]
        pass

    flags = FeatureStateSerializerFull(many=True)
    traits = TraitSerializerBasic(many=True)
    segments = SegmentSerializerBasic(many=True)


class IdentifyWithTraitsSerializer(
    HideSensitiveFieldsSerializerMixin, serializers.Serializer  # type: ignore[type-arg]
):
    identifier = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    transient = serializers.BooleanField(write_only=True, default=False)
    traits = TraitSerializerBasic(required=False, many=True)
    flags = SDKFeatureStateSerializer(read_only=True, many=True)

    sensitive_fields = ("traits",)

    def save(self, **kwargs):  # type: ignore[no-untyped-def]
        """
        Create the identity with the associated traits
        (optionally store traits if flag set on org)
        """
        identifier = self.validated_data.get("identifier")
        environment = self.context["environment"]
        transient = self.validated_data["transient"]
        sdk_trait_data: list[SDKTraitData] = self.validated_data.get("traits", [])

        if not identifier:
            # We have a fully transient identity that should never be persisted.
            identity, traits = get_transient_identity_and_traits(
                environment=environment,
                sdk_trait_data=sdk_trait_data,
            )

        elif transient:
            # Don't persist incoming data but load presently stored
            # overrides and traits, if any.
            identity, traits = get_identified_transient_identity_and_traits(
                environment=environment,
                identifier=identifier,
                sdk_trait_data=sdk_trait_data,
            )

        else:
            # Persist the identity in accordance with individual trait transiency
            # and persistence settings outside of request context.
            identity, traits = get_persisted_identity_and_traits(
                environment=environment,
                identifier=identifier,
                sdk_trait_data=sdk_trait_data,
            )

        all_feature_states = identity.get_all_feature_states(
            traits=traits,
            additional_filters=self.context.get("feature_states_additional_filters"),
        )
        identify_integrations(identity, all_feature_states, traits)  # type: ignore[no-untyped-call]

        return {
            "identity": identity,
            "identifier": identity.identifier,
            "traits": traits,
            "flags": all_feature_states,
        }

    def validate_traits(self, traits: typing.List[dict] = None):  # type: ignore[no-untyped-def,type-arg,assignment]
        request = self.context["request"]
        if traits and not request.environment.trait_persistence_allowed(request):
            raise serializers.ValidationError(
                "Setting traits not allowed with client key."
            )
        return traits
