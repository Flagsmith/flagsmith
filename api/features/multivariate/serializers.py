from flag_engine.features.models import (
    MultivariateFeatureStateValueModel as EngineMultivariateFeatureStateValueModel,
)
from flag_engine.features.schemas import MultivariateFeatureStateValueSchema
from rest_framework import serializers

from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)

engine_multi_fs_value_schema = MultivariateFeatureStateValueSchema()


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


class EdgeMultivariateFeatureStateValueSerializer(serializers.ModelSerializer):
    # custom serializer because it does not have pk
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return EngineMultivariateFeatureStateValueModel(**data)

    class Meta:
        model = MultivariateFeatureStateValue
        fields = (
            "multivariate_feature_option",
            "percentage_allocation",
        )
