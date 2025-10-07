import typing

from django.core.exceptions import ValidationError
from django.db.models import Sum
from rest_framework import serializers

from core.constants import BOOLEAN, INTEGER
from features.models import Feature, FeatureState
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


class MultivariateOptionValuesSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    value = serializers.SerializerMethodField()

    class Meta:
        model = MultivariateFeatureOption
        fields = ("value",)


def get_value(
    self: serializers.ModelSerializer[MultivariateFeatureOption],
    obj: MultivariateFeatureOption,
) -> str | int | bool | None:
    if obj.type == BOOLEAN:
        return obj.boolean_value
    if obj.type == INTEGER:
        return obj.integer_value
    return obj.string_value


class FeatureMVOptionsValuesResponseSerializer(serializers.Serializer):  # type: ignore[type-arg]
    control_value = serializers.SerializerMethodField()
    options = MultivariateOptionValuesSerializer(many=True)

    def get_control_value(self, obj: dict[str, typing.Any]) -> str | int | bool | None:
        fs: FeatureState | None = obj.get("feature_state")
        if not fs:
            return None
        value: str | int | bool | None = fs.get_feature_state_value()
        return value


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
