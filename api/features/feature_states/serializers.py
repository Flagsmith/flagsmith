from collections.abc import Sequence
from typing import TypeVar, cast

from rest_framework import serializers

from core.dataclasses import AuthorData
from environments.models import Environment
from features.feature_states.types import (
    DeleteSegmentOverridePayload,
    EnvironmentDefaultPayload,
    EnvironmentMultivariateValuePayload,
    FeatureIdentifierPayload,
    FeatureValuePayload,
    SegmentIdentifierPayload,
    SegmentOverrideMultivariateValuePayload,
    SegmentOverridePayload,
    SegmentReferencePayload,
    UpdateFlagOptionAPayload,
    UpdateFlagOptionBPayload,
)
from features.models import Feature, FeatureState
from features.versioning.dataclasses import (
    EnvironmentDefaultChangeSet,
    EnvironmentMultivariateValueChangeSet,
    FeatureValue,
    FlagChangeSetOptionA,
    FlagChangeSetOptionB,
    MultivariateOptionUpdateChangeSet,
    MultivariateValueChangeSet,
    NewMultivariateOptionChangeSet,
    SegmentOverrideChangeSet,
)
from features.versioning.versioning_service import (
    delete_segment_override,
    update_flag_option_a,
    update_flag_option_b,
)
from segments.models import Segment

_IN = TypeVar("_IN")


class BaseFeatureUpdateSerializer(serializers.Serializer[_IN]):
    @property
    def environment(self) -> Environment:
        environment: Environment | None = self.context.get("environment")
        if not environment:
            raise serializers.ValidationError("Environment context is required")
        return environment

    def get_feature(self) -> Feature:
        feature_data: FeatureIdentifierPayload = self.validated_data["feature"]
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


class FeatureIdentifierSerializer(serializers.Serializer[FeatureIdentifierPayload]):
    name = serializers.CharField(required=False, allow_blank=False)
    id = serializers.IntegerField(required=False)

    def validate(self, attrs: FeatureIdentifierPayload) -> FeatureIdentifierPayload:
        has_name = "name" in attrs
        has_id = "id" in attrs
        if not has_name and not has_id:
            raise serializers.ValidationError(
                "Either 'name' or 'id' is required for feature identification"
            )
        if has_name and has_id:
            raise serializers.ValidationError("Provide either 'name' or 'id', not both")
        return attrs


class SegmentReferenceSerializer(serializers.Serializer[SegmentReferencePayload]):
    id = serializers.IntegerField(required=True)
    priority = serializers.IntegerField(required=False, allow_null=True)


class FeatureValueSerializer(serializers.Serializer[FeatureValuePayload]):
    type = serializers.ChoiceField(
        choices=["integer", "string", "boolean"], required=True
    )
    value = serializers.CharField(required=True, allow_blank=True)

    def validate(self, attrs: FeatureValuePayload) -> FeatureValuePayload:
        value_type = attrs["type"]
        string_val = attrs["value"]

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

        return attrs


class BaseMultivariateValueSerializer(serializers.Serializer[_IN]):
    percentage_allocation = serializers.FloatField(
        required=True, min_value=0, max_value=100
    )


class SegmentOverrideMultivariateValueSerializer(
    BaseMultivariateValueSerializer[SegmentOverrideMultivariateValuePayload]
):
    multivariate_feature_option = serializers.IntegerField(required=True)
    value = FeatureValueSerializer(required=False)  # Raises ValidationError if provided


class EnvironmentMultivariateValueSerializer(
    BaseMultivariateValueSerializer[EnvironmentMultivariateValuePayload]
):
    multivariate_feature_option = serializers.IntegerField(required=False)
    value = FeatureValueSerializer(required=False)

    def validate(
        self, attrs: EnvironmentMultivariateValuePayload
    ) -> EnvironmentMultivariateValuePayload:
        if "multivariate_feature_option" not in attrs and "value" not in attrs:
            raise serializers.ValidationError(
                "A new multivariate option requires a 'value'."
            )
        return attrs


def validate_multivariate_state_values(
    feature: Feature,
    multivariate_values: Sequence[
        EnvironmentMultivariateValuePayload | SegmentOverrideMultivariateValuePayload
    ],
) -> None:
    option_ids = [
        mv["multivariate_feature_option"]
        for mv in multivariate_values
        if "multivariate_feature_option" in mv
    ]
    if not option_ids:
        return
    if len(option_ids) != len(set(option_ids)):
        raise serializers.ValidationError(
            {
                "multivariate_feature_state_values": [
                    "Multivariate options must be unique"
                ]
            }
        )
    valid = set(feature.multivariate_options.values_list("id", flat=True))
    if invalid := set(option_ids) - valid:
        raise serializers.ValidationError(
            {
                "multivariate_feature_state_values": [
                    f"Multivariate options {sorted(invalid)} do not belong to the feature"
                ]
            }
        )


def _to_environment_multivariate_value_change_set(
    multivariate_value: EnvironmentMultivariateValuePayload,
) -> EnvironmentMultivariateValueChangeSet:
    if "multivariate_feature_option" in multivariate_value:
        value = multivariate_value.get("value")
        return MultivariateOptionUpdateChangeSet(
            multivariate_feature_option_id=multivariate_value[
                "multivariate_feature_option"
            ],
            percentage_allocation=multivariate_value["percentage_allocation"],
            value=(
                FeatureValue(type_=value["type"], value=value["value"])
                if value is not None
                else None
            ),
        )
    value = multivariate_value["value"]
    return NewMultivariateOptionChangeSet(
        percentage_allocation=multivariate_value["percentage_allocation"],
        value=FeatureValue(type_=value["type"], value=value["value"]),
    )


class UpdateFlagOptionASerializer(BaseFeatureUpdateSerializer[FeatureState]):
    feature = FeatureIdentifierSerializer(required=True)
    segment = SegmentReferenceSerializer(required=False)
    enabled = serializers.BooleanField(required=False)
    value = FeatureValueSerializer(required=False)
    multivariate_feature_state_values = EnvironmentMultivariateValueSerializer(
        many=True, required=False
    )

    def validate_segment(
        self, value: SegmentReferencePayload
    ) -> SegmentReferencePayload:
        self.validate_segment_id(value["id"])
        return value

    def validate(self, attrs: UpdateFlagOptionAPayload) -> UpdateFlagOptionAPayload:
        multivariate_values = attrs.get("multivariate_feature_state_values")
        if multivariate_values is None:
            return attrs

        if "segment" in attrs:
            if any(
                "multivariate_feature_option" not in mv for mv in multivariate_values
            ):
                raise serializers.ValidationError(
                    {
                        "multivariate_feature_state_values": [
                            "Segment overrides require a variant 'id'."
                        ]
                    }
                )
            if any("value" in mv for mv in multivariate_values):
                raise serializers.ValidationError(
                    {
                        "multivariate_feature_state_values": [
                            "Segment overrides can only re-weight existing variants."
                        ]
                    }
                )
        elif sum(mv["percentage_allocation"] for mv in multivariate_values) > 100:
            raise serializers.ValidationError(
                {
                    "multivariate_feature_state_values": [
                        "Multivariate percentage values exceed 100%."
                    ]
                }
            )

        try:
            feature = Feature.objects.get(
                project_id=self.environment.project_id, **attrs["feature"]
            )
        except Feature.DoesNotExist:
            return attrs
        validate_multivariate_state_values(feature, multivariate_values)

        return attrs

    @property
    def change_set_option_a(self) -> FlagChangeSetOptionA:
        validated_data = cast(UpdateFlagOptionAPayload, self.validated_data)
        value_data = validated_data.get("value")
        segment_data = validated_data.get("segment")
        multivariate_values = validated_data.get("multivariate_feature_state_values")

        segment_multivariate_values: list[MultivariateValueChangeSet] | None = None
        environment_multivariate_values: (
            list[EnvironmentMultivariateValueChangeSet] | None
        ) = None
        if multivariate_values is not None:
            if segment_data is not None:
                segment_multivariate_values = [
                    MultivariateValueChangeSet(
                        multivariate_feature_option_id=mv[
                            "multivariate_feature_option"
                        ],
                        percentage_allocation=mv["percentage_allocation"],
                    )
                    for mv in multivariate_values
                    if "multivariate_feature_option" in mv
                ]
            else:
                environment_multivariate_values = [
                    _to_environment_multivariate_value_change_set(mv)
                    for mv in multivariate_values
                ]

        return FlagChangeSetOptionA(
            author=AuthorData.from_request(self.context["request"]),
            enabled=validated_data.get("enabled"),
            value=(
                FeatureValue(type_=value_data["type"], value=value_data["value"])
                if value_data is not None
                else None
            ),
            segment_id=segment_data["id"] if segment_data is not None else None,
            segment_priority=(
                segment_data.get("priority") if segment_data is not None else None
            ),
            multivariate_values=segment_multivariate_values,
            environment_multivariate_values=environment_multivariate_values,
        )

    def save(self, **kwargs: object) -> FeatureState:
        feature = self.get_feature()
        return update_flag_option_a(self.environment, feature, self.change_set_option_a)


class EnvironmentDefaultSerializer(serializers.Serializer[EnvironmentDefaultPayload]):
    enabled = serializers.BooleanField(required=False)
    value = FeatureValueSerializer(required=False)
    multivariate_feature_state_values = EnvironmentMultivariateValueSerializer(
        many=True, required=False
    )


class SegmentOverrideSerializer(serializers.Serializer[SegmentOverridePayload]):
    segment_id = serializers.IntegerField(required=True)
    priority = serializers.IntegerField(required=False, allow_null=True)
    enabled = serializers.BooleanField(required=False)
    value = FeatureValueSerializer(required=False)
    multivariate_feature_state_values = SegmentOverrideMultivariateValueSerializer(
        many=True, required=False
    )


class UpdateFlagOptionBSerializer(BaseFeatureUpdateSerializer[None]):
    feature = FeatureIdentifierSerializer(required=True)
    environment_default = EnvironmentDefaultSerializer(required=False)
    segment_overrides = SegmentOverrideSerializer(many=True, required=False)

    def validate_segment_overrides(
        self,
        value: list[SegmentOverridePayload],
    ) -> list[SegmentOverridePayload]:
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

    def validate(self, attrs: UpdateFlagOptionBPayload) -> UpdateFlagOptionBPayload:
        multivariate_value_lists: list[
            Sequence[
                EnvironmentMultivariateValuePayload
                | SegmentOverrideMultivariateValuePayload
            ]
        ] = []

        environment_option_ids: set[int] | None = None
        if (environment_default := attrs.get("environment_default")) is not None:
            environment_default_multivariate_values = environment_default.get(
                "multivariate_feature_state_values"
            )
            if environment_default_multivariate_values is not None:
                if (
                    sum(
                        mv["percentage_allocation"]
                        for mv in environment_default_multivariate_values
                    )
                    > 100
                ):
                    raise serializers.ValidationError(
                        {
                            "multivariate_feature_state_values": [
                                "Multivariate percentage values exceed 100%."
                            ]
                        }
                    )
                environment_option_ids = {
                    mv["multivariate_feature_option"]
                    for mv in environment_default_multivariate_values
                    if "multivariate_feature_option" in mv
                }
                multivariate_value_lists.append(environment_default_multivariate_values)

        for override in attrs.get("segment_overrides") or []:
            override_multivariate_values = override.get(
                "multivariate_feature_state_values"
            )
            if override_multivariate_values is None:
                continue
            if any("value" in mv for mv in override_multivariate_values) or (
                # The environment list is absolute: it deletes unlisted options.
                environment_option_ids is not None
                and any(
                    mv["multivariate_feature_option"] not in environment_option_ids
                    for mv in override_multivariate_values
                )
            ):
                raise serializers.ValidationError(
                    {
                        "multivariate_feature_state_values": [
                            "Segment overrides can only re-weight existing variants."
                        ]
                    }
                )
            multivariate_value_lists.append(override_multivariate_values)

        if not multivariate_value_lists:
            return attrs

        try:
            feature = Feature.objects.get(
                project_id=self.environment.project_id, **attrs["feature"]
            )
        except Feature.DoesNotExist:
            return attrs
        for multivariate_values in multivariate_value_lists:
            validate_multivariate_state_values(feature, multivariate_values)

        return attrs

    @property
    def change_set_option_b(self) -> FlagChangeSetOptionB:
        validated_data = cast(UpdateFlagOptionBPayload, self.validated_data)

        environment_default_data = validated_data.get("environment_default")
        environment_default: EnvironmentDefaultChangeSet | None = None
        if environment_default_data is not None:
            value_data = environment_default_data.get("value")
            multivariate_data = environment_default_data.get(
                "multivariate_feature_state_values"
            )
            environment_default = EnvironmentDefaultChangeSet(
                enabled=environment_default_data.get("enabled"),
                value=(
                    FeatureValue(type_=value_data["type"], value=value_data["value"])
                    if value_data is not None
                    else None
                ),
                multivariate_values=(
                    [
                        _to_environment_multivariate_value_change_set(mv)
                        for mv in multivariate_data
                    ]
                    if multivariate_data is not None
                    else None
                ),
            )

        segment_overrides = []
        for override_data in validated_data.get("segment_overrides") or []:
            override_value_data = override_data.get("value")
            override_multivariate_data = override_data.get(
                "multivariate_feature_state_values"
            )
            segment_overrides.append(
                SegmentOverrideChangeSet(
                    segment_id=override_data["segment_id"],
                    enabled=override_data.get("enabled"),
                    value=(
                        FeatureValue(
                            type_=override_value_data["type"],
                            value=override_value_data["value"],
                        )
                        if override_value_data is not None
                        else None
                    ),
                    priority=override_data.get("priority"),
                    multivariate_values=(
                        [
                            MultivariateValueChangeSet(
                                multivariate_feature_option_id=mv[
                                    "multivariate_feature_option"
                                ],
                                percentage_allocation=mv["percentage_allocation"],
                            )
                            for mv in override_multivariate_data
                        ]
                        if override_multivariate_data is not None
                        else None
                    ),
                )
            )

        return FlagChangeSetOptionB(
            author=AuthorData.from_request(self.context["request"]),
            environment_default=environment_default,
            segment_overrides=segment_overrides,
        )

    def save(self, **kwargs: object) -> None:
        feature = self.get_feature()
        update_flag_option_b(self.environment, feature, self.change_set_option_b)


class SegmentIdentifierSerializer(serializers.Serializer[SegmentIdentifierPayload]):
    id = serializers.IntegerField(required=True)


class DeleteSegmentOverrideSerializer(BaseFeatureUpdateSerializer[None]):
    feature = FeatureIdentifierSerializer(required=True)
    segment = SegmentIdentifierSerializer(required=True)

    def validate_segment(
        self, value: SegmentIdentifierPayload
    ) -> SegmentIdentifierPayload:
        self.validate_segment_id(value["id"])
        return value

    def save(self, **kwargs: object) -> None:
        feature = self.get_feature()
        validated_data = cast(DeleteSegmentOverridePayload, self.validated_data)
        segment_id = validated_data["segment"]["id"]
        author = AuthorData.from_request(self.context["request"])

        delete_segment_override(self.environment, feature, segment_id, author)
