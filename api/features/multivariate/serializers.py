from django.core.exceptions import ValidationError
from django.db.models import Sum
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

    def validate(self, attrs):
        attrs = super().validate(attrs)
        total_sibling_percentage_allocation = (
            self._get_siblings(attrs).aggregate(
                total_percentage_allocation=Sum("default_percentage_allocation")
            )["total_percentage_allocation"]
            or 0
        )
        total_percentage_allocation = (
            total_sibling_percentage_allocation + attrs["default_percentage_allocation"]
        )

        if total_percentage_allocation > 100:
            raise ValidationError("Invalid percentage allocation")

        return attrs

    def _get_siblings(self, attrs):
        siblings = attrs["feature"].multivariate_options.all()
        if attrs.get("id"):
            siblings.exclude(id=attrs.get("id"))

        return siblings

    def save(self, **kwargs):
        return super().save(**kwargs)


class MultivariateFeatureStateValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultivariateFeatureStateValue
        fields = (
            "id",
            "multivariate_feature_option",
            "percentage_allocation",
        )
