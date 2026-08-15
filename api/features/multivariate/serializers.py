import typing

from django.core.exceptions import ValidationError
from django.db.models import Sum
from rest_framework import serializers

from core.constants import BOOLEAN, INTEGER
from features.constants import CONTROL_VARIANT_KEY, RESERVED_VARIANT_KEY_MESSAGE
from features.models import Feature, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)


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
            "key",
        )
        # `key` is only writable via the dedicated mv-options endpoint
        # (`MultivariateFeatureOptionSerializer`), where its uniqueness is
        # validated.
        read_only_fields = ("uuid", "key")


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
        read_only_fields = ("uuid",)  # type: ignore[assignment]
        # `key` participates in the ("feature", "key") unique_together, which
        # makes DRF mark it as required. It is optional (nullable), so override.
        extra_kwargs = {"key": {"required": False}}

    def get_unique_together_validators(self):  # type: ignore[no-untyped-def]
        # The auto-generated `UniqueTogetherValidator` for ("feature", "key")
        # also forces `key` to be required on create. We enforce uniqueness
        # ourselves in `validate()`, with the database constraint as the final
        # guard, so drop it.
        return []

    def validate_key(self, value: str | None) -> str | None:
        if value == CONTROL_VARIANT_KEY:
            raise serializers.ValidationError(RESERVED_VARIANT_KEY_MESSAGE)
        return value

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        attrs = super().validate(attrs)
        
        # Safely get feature and allocation, falling back to instance for PATCH requests
        feature = attrs.get("feature", getattr(self.instance, "feature", None))
        default_percentage_allocation = attrs.get(
            "default_percentage_allocation", 
            getattr(self.instance, "default_percentage_allocation", 0)
        )

        total_sibling_percentage_allocation = (
            self._get_siblings(feature).aggregate(
                total_percentage_allocation=Sum("default_percentage_allocation")
            )["total_percentage_allocation"]
            or 0
        )
        
        total_percentage_allocation = (
            total_sibling_percentage_allocation + default_percentage_allocation
        )

        if total_percentage_allocation > 100:
            raise ValidationError(
                {"default_percentage_allocation": "Invalid percentage allocation"}
            )

        if self.instance is None:
            # Creating an option adds `default_percentage_allocation` to every
            # environment's default feature state (see `MultivariateFeatureOption
            # .create_multivariate_feature_state_values`). A given environment's
            # actual feature state values can have drifted from the option-level
            # defaults checked above (e.g. via a per-environment edit), so check
            # those too rather than allowing that step to silently push one
            # environment over 100%.
            self._validate_environment_allocations(
                feature, default_percentage_allocation
            )

        self._validate_key_is_unique(attrs)

        return attrs

    def _validate_environment_allocations(
        self, feature: Feature, default_percentage_allocation: float
    ) -> None:
        environment_overflows = (
            MultivariateFeatureStateValue.objects.filter(
                feature_state__in=feature.feature_states.filter(
                    identity=None, feature_segment=None
                ),
            )
            .values("feature_state_id")
            .annotate(total_percentage_allocation=Sum("percentage_allocation"))
            .filter(total_percentage_allocation__gt=100 - default_percentage_allocation)
            .exists()
        )
        if environment_overflows:
            raise ValidationError(
                {"default_percentage_allocation": "Invalid percentage allocation"}
            )

    def _validate_key_is_unique(self, attrs: dict[str, typing.Any]) -> None:
        key = attrs.get("key")
        if key is None:
            return
        feature = attrs.get("feature",getattr(self.instance, "feature",None))
        if self._get_siblings(feature).filter(key=key).exists():
            raise ValidationError(
                {
                    "key": "Multivariate option with this key already exists for the feature."
                }
            )

    def _get_siblings(self, feature: Feature):  # type: ignore[no-untyped-def]
        siblings = feature.multivariate_options.all()
        if self.instance:
            siblings = siblings.exclude(id=self.instance.id)  # type: ignore[union-attr]

        return siblings
