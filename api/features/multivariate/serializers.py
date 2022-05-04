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
            "feature",
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
