import typing

from drf_spectacular.utils import extend_schema_field
from flagsmith_schemas.dynamodb import FeatureState as EdgeFeatureState
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from environments.identities.models import Identity
from evaluation.types import EvaluatedFeatureState
from features.models import FeatureState


class IdentifierOnlyIdentitySerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Identity
        fields = ("identifier",)


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
        if isinstance(instance, typing.Mapping):
            return instance["value"]  # type: ignore[no-any-return]
        return instance.value  # type: ignore[no-any-return]


class IdentityAllFeatureStatesMVFeatureStateValueSerializer(serializers.Serializer):  # type: ignore[type-arg]
    multivariate_feature_option = IdentityAllFeatureStatesMVFeatureOptionSerializer()
    percentage_allocation = serializers.FloatField()


class IdentityAllFeatureStatesSerializer(serializers.Serializer):  # type: ignore[type-arg]
    feature = IdentityAllFeatureStatesFeatureSerializer(source="feature_state.feature")
    enabled = serializers.BooleanField(source="evaluation_result.enabled")
    feature_state_value = serializers.SerializerMethodField(
        help_text="Can be any of the following types: integer, boolean, string."
    )
    overridden_by = serializers.SerializerMethodField(
        help_text="One of: null, 'SEGMENT', 'IDENTITY'."
    )
    segment = serializers.SerializerMethodField()
    multivariate_feature_state_values = (
        IdentityAllFeatureStatesMVFeatureStateValueSerializer(
            source="feature_state.multivariate_feature_state_values", many=True
        )
    )

    def get_feature_state_value(
        self, instance: "EvaluatedFeatureState[FeatureState | EdgeFeatureState]"
    ) -> typing.Union[str, int, bool]:
        return instance.evaluation_result["value"]  # type: ignore[no-any-return]

    def get_overridden_by(
        self, instance: "EvaluatedFeatureState[FeatureState | EdgeFeatureState]"
    ) -> typing.Optional[str]:
        feature_state = instance.feature_state
        if not isinstance(feature_state, FeatureState):
            # An edge identity's overrides are the only feature states
            # reaching this serialiser that are not ORM rows.
            return "IDENTITY"
        if feature_state.feature_segment_id is not None:
            return "SEGMENT"
        if feature_state.identity_id is not None:
            return "IDENTITY"
        return None

    @extend_schema_field(IdentityAllFeatureStatesSegmentSerializer)
    def get_segment(
        self, instance: "EvaluatedFeatureState[FeatureState | EdgeFeatureState]"
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        feature_state = instance.feature_state
        if (
            isinstance(feature_state, FeatureState)
            and (feature_segment := feature_state.feature_segment) is not None
        ):
            return IdentityAllFeatureStatesSegmentSerializer(
                instance=feature_segment.segment
            ).data
        return None


class IdentitySourceIdentityRequestSerializer(serializers.Serializer):  # type: ignore[type-arg]
    source_identity_id = serializers.IntegerField(
        required=True,
        help_text="ID of the source identity to clone feature states from.",
    )
