from rest_framework import exceptions, serializers

from core.constants import INTEGER
from environments.identities.models import Identity
from environments.identities.serializers import IdentitySerializer
from environments.identities.traits.fields import TraitValueField
from environments.identities.traits.models import Trait


class TraitSerializerFull(serializers.ModelSerializer):  # type: ignore[type-arg]
    identity = IdentitySerializer()
    trait_value = serializers.SerializerMethodField()

    class Meta:
        model = Trait
        fields = "__all__"

    @staticmethod
    def get_trait_value(obj):  # type: ignore[no-untyped-def]
        return obj.get_trait_value()


class TraitSerializerBasic(serializers.ModelSerializer):  # type: ignore[type-arg]
    trait_value = TraitValueField(allow_null=True)
    transient = serializers.BooleanField(default=False)

    class Meta:
        model = Trait
        fields = ("id", "trait_key", "trait_value", "transient")
        read_only_fields = ("id",)


class IncrementTraitValueSerializer(serializers.Serializer):  # type: ignore[type-arg]
    trait_key = serializers.CharField()
    increment_by = serializers.IntegerField(write_only=True)
    identifier = serializers.CharField()
    trait_value = serializers.IntegerField(read_only=True)

    def to_representation(self, instance):  # type: ignore[no-untyped-def]
        return {
            "trait_key": instance.trait_key,
            "trait_value": instance.integer_value,
            "identifier": instance.identity.identifier,
        }

    def create(self, validated_data):  # type: ignore[no-untyped-def]
        trait, _ = Trait.objects.get_or_create(
            **self._build_query_data(validated_data),  # type: ignore[no-untyped-call]
            defaults=self._build_default_data(),  # type: ignore[no-untyped-call]
        )

        if trait.value_type != INTEGER:
            raise exceptions.ValidationError("Trait is not an integer.")

        trait.integer_value += validated_data.get("increment_by")
        trait.save()  # type: ignore[no-untyped-call]
        return trait

    def _build_query_data(self, validated_data):  # type: ignore[no-untyped-def]
        identity_data = {
            "identifier": validated_data.get("identifier"),
            "environment": self.context.get("request").environment,  # type: ignore[union-attr]
        }
        identity, _ = Identity.objects.get_or_create(**identity_data)

        return {"trait_key": validated_data.get("trait_key"), "identity": identity}

    def _build_default_data(self):  # type: ignore[no-untyped-def]
        return {"value_type": INTEGER, "integer_value": 0}

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        request = self.context["request"]
        if not request.environment.trait_persistence_allowed(request):
            raise serializers.ValidationError(
                "Setting traits not allowed with client key."
            )
        return attrs


class TraitKeysSerializer(serializers.Serializer):  # type: ignore[type-arg]
    keys = serializers.ListSerializer(child=serializers.CharField())  # type: ignore[var-annotated]


class DeleteAllTraitKeysSerializer(serializers.Serializer):  # type: ignore[type-arg]
    key = serializers.CharField()

    def delete(self):  # type: ignore[no-untyped-def]
        environment = self.context.get("environment")
        Trait.objects.filter(
            identity__environment=environment, trait_key=self.validated_data.get("key")
        ).delete()


class TraitSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Trait
        fields = (
            "id",
            "trait_key",
            "value_type",
            "integer_value",
            "string_value",
            "boolean_value",
            "float_value",
            "created_date",
        )
