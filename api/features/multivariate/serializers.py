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

    def get_value(self, obj) -> str | int | bool | None:  # type: ignore[no-untyped-def]
        if obj.type == BOOLEAN:
            return bool(obj.boolean_value)
        if obj.type == INTEGER:
            return int(obj.integer_value)
        return str(obj.string_value)


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

        # For partial updates or nested routes, use existing instance or URL value as fallback
        feature = attrs.get("feature")
        if feature is None and self.instance is not None:
            feature = self.instance.feature

        if feature is None:
            view = self.context.get("view")
            feature_pk = getattr(view, "kwargs", {}).get("feature_pk") if view else None
            project_pk = getattr(view, "kwargs", {}).get("project_pk") if view else None
            if feature_pk is not None:
                qs = Feature.objects.filter(pk=feature_pk)
                if project_pk is not None:
                    qs = qs.filter(project__id=project_pk)
                feature = qs.first()

        if feature is None:
            raise serializers.ValidationError({"feature": "Feature is required"})

        # Ensure feature is always present in validated data (e.g. for creates via nested routes)
        attrs["feature"] = feature

        # Handle legacy records where default_percentage_allocation may be NULL in the database.
        if self.instance and self.instance.default_percentage_allocation is not None:
            instance_default_allocation = self.instance.default_percentage_allocation
        else:
            instance_default_allocation = 100

        default_allocation = attrs.get(
            "default_percentage_allocation",
            instance_default_allocation,
        )

        total_sibling_percentage_allocation = (
            self._get_siblings(feature).aggregate(
                total_percentage_allocation=Sum("default_percentage_allocation")
            )["total_percentage_allocation"]
            or 0
        )
        total_percentage_allocation = (
            total_sibling_percentage_allocation + default_allocation
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
