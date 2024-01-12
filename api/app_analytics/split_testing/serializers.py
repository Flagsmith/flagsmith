from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers

from environments.identities.models import Identity
from features.serializers import FeatureSerializer
from features.value_types import BOOLEAN, INTEGER, STRING

from .models import ConversionEvent, ConversionEventType, SplitTest


class ConversionEventSerializer(serializers.Serializer):
    identity_identifier = serializers.CharField(required=True)
    type = serializers.CharField(required=True)

    def save(self, *args, **kwargs) -> ConversionEvent:
        environment = self.context["request"].environment
        identity = Identity.objects.get(
            environment=environment,
            identifier=self.validated_data["identity_identifier"],
        )
        conversion_event_type, __ = ConversionEventType.objects.get_or_create(
            environment=environment,
            name=self.validated_data["type"],
        )
        return ConversionEvent.objects.create(
            type=conversion_event_type,
            environment=environment,
            identity=identity,
        )


class ValueDataSerializer(serializers.Serializer):
    integer_value = serializers.IntegerField()
    boolean_value = serializers.BooleanField()
    string_value = serializers.CharField()
    type = serializers.ChoiceField([BOOLEAN, STRING, INTEGER])


class SplitTestSerializer(serializers.ModelSerializer):
    feature = FeatureSerializer()
    value_data = serializers.SerializerMethodField()

    class Meta:
        model = SplitTest
        fields = (
            "feature",
            "evaluation_count",
            "conversion_count",
            "value_data",
            "pvalue",
        )

    @swagger_auto_schema(serializer_or_field=ValueDataSerializer())
    def get_value_data(self, instance: SplitTest) -> dict:
        if instance.multivariate_feature_option:
            return ValueDataSerializer(
                instance=instance.multivariate_feature_option
            ).data

        feature_state = self.context["feature_states_by_env_feature_pair"][
            (instance.environment_id, instance.feature_id)
        ]

        return ValueDataSerializer(instance=feature_state.feature_state_value).data


class ConversionEventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversionEventType
        fields = (
            "name",
            "created_at",
            "updated_at",
        )


class ConversionEventTypeQuerySerializer(serializers.Serializer):
    environment_id = serializers.IntegerField()


class SplitTestQuerySerializer(serializers.Serializer):
    conversion_event_type_id = serializers.IntegerField()
