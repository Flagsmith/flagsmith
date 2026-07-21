import typing

import pytest
from rest_framework import serializers

from environments.models import Environment
from features.feature_states.serializers import (
    FeatureValueSerializer,
    UpdateFlagSerializer,
    UpdateFlagV2Serializer,
    validate_multivariate_state_values,
)
from features.models import Feature
from projects.models import Project
from segments.models import Segment


def test_get_feature__no_environment_in_context__raises_validation_error(
    feature: Feature,
) -> None:
    # Given
    serializer = UpdateFlagSerializer(
        data={
            "feature": {"name": feature.name},
            "enabled": True,
            "value": {"type": "string", "value": "test"},
        },
        context={},  # No environment
    )
    serializer.is_valid()

    # When
    with pytest.raises(serializers.ValidationError) as exc_info:
        serializer.get_feature()

    # Then
    assert "Environment context is required" in str(exc_info.value)


def test_validate_segment_overrides__empty_list__returns_empty_list() -> None:
    # Given
    serializer = UpdateFlagV2Serializer()

    # When
    result = serializer.validate_segment_overrides([])

    # Then
    assert result == []


def test_feature_value_serializer__invalid_integer__returns_not_valid() -> None:
    # Given
    serializer = FeatureValueSerializer(
        data={"type": "integer", "value": "not_a_number"}
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert "not a valid integer" in str(serializer.errors)


def test_feature_value_serializer__invalid_boolean__returns_not_valid() -> None:
    # Given
    serializer = FeatureValueSerializer(data={"type": "boolean", "value": "yes"})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert "not a valid boolean" in str(serializer.errors)


@pytest.mark.parametrize(
    "serializer_class,data_factory",
    [
        (
            UpdateFlagSerializer,
            lambda feature, segment_id: {
                "feature": {"name": feature.name},
                "segment": {"id": segment_id},
                "enabled": True,
                "value": {"type": "string", "value": "test"},
            },
        ),
        (
            UpdateFlagV2Serializer,
            lambda feature, segment_id: {
                "feature": {"name": feature.name},
                "environment_default": {
                    "enabled": True,
                    "value": {"type": "string", "value": "default"},
                },
                "segment_overrides": [
                    {
                        "segment_id": segment_id,
                        "enabled": True,
                        "value": {"type": "string", "value": "test"},
                    },
                ],
            },
        ),
    ],
)
def test_update_flag_serializer__nonexistent_segment__returns_invalid(
    feature: Feature,
    environment: Environment,
    serializer_class: type,
    data_factory: typing.Callable[[Feature, int], dict],  # type: ignore[type-arg]
) -> None:
    # Given
    serializer = serializer_class(
        data=data_factory(feature, 999999),
        context={"environment": environment},
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert "not found in project" in str(serializer.errors)


@pytest.mark.parametrize(
    "serializer_class,data_factory",
    [
        (
            UpdateFlagSerializer,
            lambda feature, segment_id: {
                "feature": {"name": feature.name},
                "segment": {"id": segment_id},
                "enabled": True,
                "value": {"type": "string", "value": "test"},
            },
        ),
        (
            UpdateFlagV2Serializer,
            lambda feature, segment_id: {
                "feature": {"name": feature.name},
                "environment_default": {
                    "enabled": True,
                    "value": {"type": "string", "value": "default"},
                },
                "segment_overrides": [
                    {
                        "segment_id": segment_id,
                        "enabled": True,
                        "value": {"type": "string", "value": "test"},
                    },
                ],
            },
        ),
    ],
)
def test_update_flag_serializer__cross_project_segment__returns_invalid(
    feature: Feature,
    environment: Environment,
    organisation: object,
    serializer_class: type,
    data_factory: typing.Callable[[Feature, int], dict],  # type: ignore[type-arg]
) -> None:
    # Given
    other_project = Project.objects.create(
        name="Other Project",
        organisation=organisation,
    )
    other_segment = Segment.objects.create(name="other_segment", project=other_project)
    serializer = serializer_class(
        data=data_factory(feature, other_segment.id),
        context={"environment": environment},
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert "not found in project" in str(serializer.errors)


def test_update_flag_v2_serializer__mv_option_not_on_feature__returns_invalid(
    multivariate_feature: Feature,
    environment: Environment,
    segment: Segment,
) -> None:
    # Given
    serializer = UpdateFlagV2Serializer(
        data={
            "feature": {"name": multivariate_feature.name},
            "environment_default": {
                "enabled": True,
                "value": {"type": "string", "value": "default"},
            },
            "segment_overrides": [
                {
                    "segment_id": segment.id,
                    "enabled": True,
                    "value": {"type": "string", "value": "test"},
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": 999999,
                            "percentage_allocation": 100,
                        }
                    ],
                },
            ],
        },
        context={"environment": environment},
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert "do not belong to the feature" in str(serializer.errors)


def test_update_flag_v2_serializer__duplicate_mv_option__returns_invalid(
    multivariate_feature: Feature,
    multivariate_options: list[typing.Any],
    environment: Environment,
    segment: Segment,
) -> None:
    # Given the same multivariate option is passed twice
    option = multivariate_options[0]
    serializer = UpdateFlagV2Serializer(
        data={
            "feature": {"name": multivariate_feature.name},
            "environment_default": {
                "enabled": True,
                "value": {"type": "string", "value": "default"},
            },
            "segment_overrides": [
                {
                    "segment_id": segment.id,
                    "enabled": True,
                    "value": {"type": "string", "value": "test"},
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": option.id,
                            "percentage_allocation": 40,
                        },
                        {
                            "multivariate_feature_option": option.id,
                            "percentage_allocation": 60,
                        },
                    ],
                },
            ],
        },
        context={"environment": environment},
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert "must be unique" in str(serializer.errors)


def test_validate_multivariate_state_values__empty_list__is_noop(
    feature: Feature,
) -> None:
    # Given
    multivariate_values: list[dict[str, typing.Any]] = []

    # When / Then no exception is raised
    validate_multivariate_state_values(feature, multivariate_values)


def test_update_flag_v2_serializer__valid_mv_option__change_set_carries_mv(
    multivariate_feature: Feature,
    multivariate_options: list,  # type: ignore[type-arg]
    environment: Environment,
    segment: Segment,
    admin_user: typing.Any,
    rf: typing.Any,
) -> None:
    # Given
    option = multivariate_options[0]
    request = rf.post("/")
    request.user = admin_user
    serializer = UpdateFlagV2Serializer(
        data={
            "feature": {"name": multivariate_feature.name},
            "environment_default": {
                "enabled": True,
                "value": {"type": "string", "value": "default"},
            },
            "segment_overrides": [
                {
                    "segment_id": segment.id,
                    "enabled": True,
                    "value": {"type": "string", "value": "test"},
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": option.id,
                            "percentage_allocation": 75,
                        }
                    ],
                },
            ],
        },
        context={"environment": environment, "request": request},
    )

    # When
    is_valid = serializer.is_valid()
    change_set = serializer.change_set_v2

    # Then
    assert is_valid is True
    mv_values = change_set.segment_overrides[0].multivariate_values
    assert mv_values is not None
    assert mv_values[0].multivariate_feature_option_id == option.id
    assert mv_values[0].percentage_allocation == 75
