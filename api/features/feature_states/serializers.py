from rest_framework import serializers

from environments.models import Environment
from features.models import Feature, FeatureState
from features.versioning.dataclasses import (
    AuthorData,
    FlagChangeSet,
    FlagChangeSetV2,
    SegmentOverrideChangeSet,
)
from features.versioning.versioning_service import update_flag, update_flag_v2
from segments.models import Segment


class BaseFeatureUpdateSerializer(serializers.Serializer):  # type: ignore[type-arg]
    @property
    def environment(self) -> Environment:
        environment: Environment | None = self.context.get("environment")
        if not environment:
            raise serializers.ValidationError("Environment context is required")
        return environment

    def get_feature(self) -> Feature:
        feature_data = self.validated_data["feature"]
        try:
            feature: Feature = Feature.objects.get(
                project_id=self.environment.project_id, **feature_data
            )
            return feature
        except Feature.DoesNotExist:
            raise serializers.ValidationError(
                f"Feature '{feature_data}' not found in project"
            )

    def validate_segment_id(self, segment_id: int) -> None:
        if not Segment.objects.filter(
            id=segment_id, project_id=self.environment.project_id
        ).exists():
            raise serializers.ValidationError(
                f"Segment with id {segment_id} not found in project"
            )


class FeatureIdentifierSerializer(serializers.Serializer):  # type: ignore[type-arg]
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


class FeatureUpdateSegmentDataSerializer(serializers.Serializer):  # type: ignore[type-arg]
    id = serializers.IntegerField(required=True)
    priority = serializers.IntegerField(required=False, allow_null=True)


class FeatureValueSerializer(serializers.Serializer):  # type: ignore[type-arg]
    type = serializers.ChoiceField(
        choices=["integer", "string", "boolean"], required=True
    )
    value = serializers.CharField(required=True, allow_blank=True)

    def validate(self, data: dict) -> dict:  # type: ignore[type-arg]
        value_type = data["type"]
        string_val = data["value"]

        if value_type == "integer":
            try:
                int(string_val)
            except ValueError:
                raise serializers.ValidationError(
                    f"'{string_val}' is not a valid integer"
                )
        elif value_type == "boolean":
            if string_val.lower() not in ("true", "false"):
                raise serializers.ValidationError(
                    f"'{string_val}' is not a valid boolean (use 'true' or 'false')"
                )

        return data


class UpdateFlagSerializer(BaseFeatureUpdateSerializer):
    feature = FeatureIdentifierSerializer(required=True)
    segment = FeatureUpdateSegmentDataSerializer(required=False)
    enabled = serializers.BooleanField(required=True)
    value = FeatureValueSerializer(required=True)

    def validate_segment(self, value: dict) -> dict:  # type: ignore[type-arg]
        if value and value.get("id"):
            self.validate_segment_id(value["id"])
        return value

    @property
    def flag_change_set(self) -> FlagChangeSet:
        validated_data = self.validated_data
        value_data = validated_data["value"]
        segment_data = validated_data.get("segment")

        return FlagChangeSet(
            author=AuthorData.from_request(self.context["request"]),
            enabled=validated_data["enabled"],
            feature_state_value=value_data["value"],
            type_=value_data["type"],
            segment_id=segment_data.get("id") if segment_data else None,
            segment_priority=segment_data.get("priority") if segment_data else None,
        )

    def save(self, **kwargs: object) -> FeatureState:
        feature = self.get_feature()
        return update_flag(self.environment, feature, self.flag_change_set)


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

        # TODO: optimise this once out of experimentation
        for segment_id in segment_ids:
            self.validate_segment_id(segment_id)

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
                feature_state_value=value_data["value"],
                type_=value_data["type"],
                priority=override_data.get("priority"),
            )
            segment_overrides.append(segment_override)

        return FlagChangeSetV2(
            author=AuthorData.from_request(self.context["request"]),
            environment_default_enabled=env_default["enabled"],
            environment_default_value=env_value_data["value"],
            environment_default_type=env_value_data["type"],
            segment_overrides=segment_overrides,
        )

    def save(self, **kwargs: object) -> None:
        feature = self.get_feature()
        update_flag_v2(self.environment, feature, self.change_set_v2)
