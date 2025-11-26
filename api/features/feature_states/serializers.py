import typing

from django.db.models import Q
from rest_framework import serializers

from environments.models import Environment
from features.models import Feature, FeatureState
from features.versioning.dataclasses import (
    FlagChangeSet,
    FlagChangeSetV2,
    SegmentOverrideChangeSet,
)
from features.versioning.versioning_service import update_flag, update_flag_v2
from users.models import FFAdminUser


class BaseFeatureUpdateSerializer(serializers.Serializer):  # type: ignore[type-arg]
    def get_feature(self) -> Feature:
        feature_data = self.validated_data["feature"]
        environment: Environment = self.context.get("environment")  # type: ignore[assignment]

        if not environment:
            raise serializers.ValidationError("Environment context is required")

        try:
            # TODO: strip out the id vs name piece as this is ugly as heck.
            query = Q(project_id=environment.project_id) & (
                Q(id=feature_data.get("id")) | Q(name=feature_data.get("name"))
            )
            feature: Feature = Feature.objects.get(query)
            return feature
        except Feature.DoesNotExist:
            identifier = feature_data.get("id") or feature_data.get("name")
            raise serializers.ValidationError(
                f"Feature with identifier '{identifier}' not found in project"
            )

    def _add_audit_fields(
        self, change_set: typing.Union[FlagChangeSet, FlagChangeSetV2]
    ) -> None:
        request = self.context["request"]
        if type(request.user) is FFAdminUser:
            change_set.user = request.user
        else:
            change_set.api_key = request.user.key

    def _parse_feature_value(self, value_data: dict) -> typing.Any:  # type: ignore[type-arg]
        value_serializer = FeatureValueSerializer(data=value_data)
        value_serializer.is_valid()
        return value_serializer.get_typed_value()


class FeatureIdentifierSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Accepts either name OR id (mutually exclusive)."""

    name = serializers.CharField(required=False, allow_blank=False)
    id = serializers.IntegerField(required=False)

    def validate(self, data: dict) -> dict:  # type: ignore[type-arg]
        if not data.get("name") and not data.get("id"):
            raise serializers.ValidationError(
                "Either 'name' or 'id' is required for feature identification"
            )
        if data.get("name") and data.get("id"):
            raise serializers.ValidationError("Provide either 'name' or 'id', not both")
        return data


class SegmentSerializer(serializers.Serializer):  # type: ignore[type-arg]
    id = serializers.IntegerField(required=True)
    priority = serializers.IntegerField(required=False, allow_null=True)


class FeatureValueSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Value is always a string; type field indicates how to parse it."""

    type = serializers.ChoiceField(
        choices=["integer", "string", "boolean", "float"], required=True
    )
    string_value = serializers.CharField(required=True, allow_blank=True)

    def get_typed_value(self) -> typing.Any:
        value_type = self.validated_data["type"]
        string_val = self.validated_data["string_value"]

        match value_type:
            case "string":
                return string_val
            case "integer":
                return int(string_val)
            case "boolean":
                return string_val.lower() == "true"
            case "float":
                return float(string_val)

        return string_val


class UpdateFlagSerializer(BaseFeatureUpdateSerializer):
    feature = FeatureIdentifierSerializer(required=True)
    segment = SegmentSerializer(required=False)
    enabled = serializers.BooleanField(required=True)
    value = FeatureValueSerializer(required=True)

    @property
    def flag_change_set(self) -> FlagChangeSet:
        validated_data = self.validated_data
        value_data = validated_data["value"]
        segment_data = validated_data.get("segment")

        change_set = FlagChangeSet(
            enabled=validated_data["enabled"],
            feature_state_value=self._parse_feature_value(value_data),
            type_=value_data["type"],
            segment_id=segment_data.get("id") if segment_data else None,
            segment_priority=segment_data.get("priority") if segment_data else None,
        )

        self._add_audit_fields(change_set)
        return change_set

    def save(self, **kwargs: typing.Any) -> FeatureState:
        environment: Environment = kwargs["environment"]
        feature: Feature = self.get_feature()

        return update_flag(environment, feature, self.flag_change_set)


class EnvironmentDefaultSerializer(serializers.Serializer):  # type: ignore[type-arg]
    enabled = serializers.BooleanField(required=True)
    value = FeatureValueSerializer(required=True)


class SegmentOverrideSerializer(serializers.Serializer):  # type: ignore[type-arg]
    segment_id = serializers.IntegerField(required=True)
    priority = serializers.IntegerField(required=False, allow_null=True)
    enabled = serializers.BooleanField(required=True)
    value = FeatureValueSerializer(required=True)


class UpdateFlagV2Serializer(BaseFeatureUpdateSerializer):
    feature = FeatureIdentifierSerializer(required=True)
    environment_default = EnvironmentDefaultSerializer(required=True)
    segment_overrides = SegmentOverrideSerializer(many=True, required=False)

    def validate_segment_overrides(
        self,
        value: list[dict],  # type: ignore[type-arg]
    ) -> list[dict]:  # type: ignore[type-arg]
        if not value:
            return value

        segment_ids = [override["segment_id"] for override in value]
        if len(segment_ids) != len(set(segment_ids)):
            raise serializers.ValidationError(
                "Duplicate segment_id values are not allowed"
            )

        return value

    @property
    def change_set_v2(self) -> FlagChangeSetV2:
        validated_data = self.validated_data

        env_default = validated_data["environment_default"]
        env_value_data = env_default["value"]

        segment_overrides_data = validated_data.get("segment_overrides", [])
        segment_overrides = []

        for override_data in segment_overrides_data:
            value_data = override_data["value"]

            segment_override = SegmentOverrideChangeSet(
                segment_id=override_data["segment_id"],
                enabled=override_data["enabled"],
                feature_state_value=self._parse_feature_value(value_data),
                type_=value_data["type"],
                priority=override_data.get("priority"),
            )
            segment_overrides.append(segment_override)

        change_set = FlagChangeSetV2(
            environment_default_enabled=env_default["enabled"],
            environment_default_value=self._parse_feature_value(env_value_data),
            environment_default_type=env_value_data["type"],
            segment_overrides=segment_overrides,
        )

        self._add_audit_fields(change_set)
        return change_set

    def save(self, **kwargs: typing.Any) -> dict:  # type: ignore[type-arg]
        environment: Environment = kwargs["environment"]
        feature: Feature = self.get_feature()

        return update_flag_v2(environment, feature, self.change_set_v2)
