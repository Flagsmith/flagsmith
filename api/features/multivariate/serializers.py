from django.core.exceptions import ValidationError
from django.db.models import Sum
from rest_framework import serializers

from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption


class NestedMultivariateFeatureOptionSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = MultivariateFeatureOption

        fields = (
            "id",
            "uuid",
            "type",
            "integer_value",
            "string_value",
            "boolean_value",
            "default_percentage_allocation",
        )
        read_only_fields = ("uuid",)


class MultivariateFeatureOptionSerializer(NestedMultivariateFeatureOptionSerializer):
    class Meta(NestedMultivariateFeatureOptionSerializer.Meta):
        fields = NestedMultivariateFeatureOptionSerializer.Meta.fields + ("feature",)  # type: ignore[assignment]

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        attrs = super().validate(attrs)
        total_sibling_percentage_allocation = (
            self._get_siblings(attrs["feature"]).aggregate(
                total_percentage_allocation=Sum("default_percentage_allocation")
            )["total_percentage_allocation"]
            or 0
        )
        total_percentage_allocation = (
            total_sibling_percentage_allocation + attrs["default_percentage_allocation"]
        )

        if total_percentage_allocation > 100:
            raise ValidationError(
                {"default_percentage_allocation": "Invalid percentage allocation"}
            )

        return attrs

    def _get_siblings(self, feature: Feature):  # type: ignore[no-untyped-def]
        siblings = feature.multivariate_options.all()
        if self.instance:
            siblings = siblings.exclude(id=self.instance.id)  # type: ignore[union-attr]

        return siblings
