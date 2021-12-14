from rest_framework import serializers

from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)


class MultivariateFeatureOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultivariateFeatureOption

        fields = (
            "id",
            "type",
            "integer_value",
            "string_value",
            "boolean_value",
            "default_percentage_allocation",
        )


class MultivariateFeatureStateValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultivariateFeatureStateValue
        fields = (
            "id",
            "multivariate_feature_option",
            "percentage_allocation",
        )


class EdgeMultivariateFeatureOptionSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = MultivariateFeatureOption
        fields = ("value",)

    def get_value(self, obj):
        return obj.value


class EdgeMultivariateFeatureStateValueSerializer(serializers.ModelSerializer):
    # custom serializer because it does not have pk
    multivariate_feature_option = EdgeMultivariateFeatureOptionSerializer()

    class Meta:
        model = MultivariateFeatureStateValue
        fields = (
            "multivariate_feature_option",
            "percentage_allocation",
        )
