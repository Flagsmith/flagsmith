import typing

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from environments.identities.models import Identity
from environments.models import Environment
from environments.serializers import EnvironmentSerializerFull
from features.evaluation import evaluate_feature_state
from features.models import FeatureState
from features.serializers import FeatureStateSerializerFull
from util.engine_models.features.models import FeatureStateModel


class IdentifierOnlyIdentitySerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Identity
        fields = ("identifier",)


class IdentitySerializerFull(serializers.ModelSerializer):  # type: ignore[type-arg]
    identity_features = FeatureStateSerializerFull(many=True)
    environment = EnvironmentSerializerFull()

    class Meta:
        model = Identity
        fields = ("id", "identifier", "identity_features", "environment")


class IdentitySerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Identity
        fields = ("id", "identifier", "environment")
        read_only_fields = ("id", "environment")

    def save(self, **kwargs):  # type: ignore[no-untyped-def]
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


class SDKIdentitiesQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    identifier = serializers.CharField(required=True)
    transient = serializers.BooleanField(default=False)


class IdentityAllFeatureStatesFeatureSerializer(serializers.Serializer):  # type: ignore[type-arg]
    id = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()


class IdentityAllFeatureStatesSegmentSerializer(serializers.Serializer):  # type: ignore[type-arg]
    id = serializers.IntegerField()
    name = serializers.CharField()


class IdentityAllFeatureStatesMVFeatureOptionSerializer(serializers.Serializer):  # type: ignore[type-arg]
    value = serializers.SerializerMethodField(
        help_text="Can be any of the following types: integer, boolean, string."
    )

    def get_value(self, instance) -> typing.Union[str, int, bool]:  # type: ignore[no-untyped-def]
        return instance.value  # type: ignore[no-any-return]


class IdentityAllFeatureStatesMVFeatureStateValueSerializer(serializers.Serializer):  # type: ignore[type-arg]
    multivariate_feature_option = IdentityAllFeatureStatesMVFeatureOptionSerializer()
    percentage_allocation = serializers.FloatField()


class IdentityAllFeatureStatesSerializer(serializers.Serializer):  # type: ignore[type-arg]
    feature = IdentityAllFeatureStatesFeatureSerializer()
    enabled = serializers.BooleanField()
    feature_state_value = serializers.SerializerMethodField(
        help_text="Can be any of the following types: integer, boolean, string."
    )
    overridden_by = serializers.SerializerMethodField(
        help_text="One of: null, 'SEGMENT', 'IDENTITY'."
    )
    segment = serializers.SerializerMethodField()
    multivariate_feature_state_values = (
        IdentityAllFeatureStatesMVFeatureStateValueSerializer(many=True)
    )

    @property
    def _identity_hash_key(self) -> str:
        environment = Environment.get_from_cache(self.context["environment_api_key"])
        assert environment
        return self.context["identity"].get_hash_key(  # type: ignore[no-any-return]
            environment.use_identity_composite_key_for_hashing
        )

    def get_feature_state_value(
        self, instance: typing.Union[FeatureState, FeatureStateModel]
    ) -> typing.Union[str, int, bool]:
        if isinstance(instance, FeatureState):
            if (flag_result := instance.flag_result) is not None:
                return flag_result["value"]  # type: ignore[no-any-return]
            # An edge identity's overrides live in DynamoDB, so these rows were
            # read straight from the ORM and never evaluated. Only multivariate
            # allocation is left to resolve.
            return evaluate_feature_state(  # type: ignore[no-any-return]
                instance, self._identity_hash_key
            )["value"]

        return instance.get_value(self._identity_hash_key)  # type: ignore[no-any-return]

    def get_overridden_by(self, instance) -> typing.Optional[str]:  # type: ignore[no-untyped-def]
        if getattr(instance, "feature_segment_id", None) is not None:
            return "SEGMENT"
        elif getattr(
            instance, "identity_id", None
        ) or instance.feature.name in self.context.get("identity_feature_names", []):
            return "IDENTITY"
        return None

    @extend_schema_field(IdentityAllFeatureStatesSegmentSerializer)
    def get_segment(self, instance) -> typing.Optional[typing.Dict[str, typing.Any]]:  # type: ignore[no-untyped-def]
        if getattr(instance, "feature_segment_id", None) is not None:
            return IdentityAllFeatureStatesSegmentSerializer(
                instance=instance.feature_segment.segment
            ).data
        return None


class IdentitySourceIdentityRequestSerializer(serializers.Serializer):  # type: ignore[type-arg]
    source_identity_id = serializers.IntegerField(
        required=True,
        help_text="ID of the source identity to clone feature states from.",
    )
