import typing

import pytest
from rest_framework import serializers

from environments.models import Environment
from features.feature_states.serializers import (
    FeatureValueSerializer,
    UpdateFlagSerializer,
    UpdateFlagV2Serializer,
)
from features.models import Feature
from projects.models import Project
from segments.models import Segment


def test_get_feature_raises_error_when_environment_not_in_context(
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


def test_validate_segment_overrides_returns_empty_list() -> None:
    # Given
    serializer = UpdateFlagV2Serializer()

    # When
    result = serializer.validate_segment_overrides([])

    # Then
    assert result == []


def test_feature_value_serializer_rejects_invalid_integer() -> None:
    # Given
    serializer = FeatureValueSerializer(
        data={"type": "integer", "value": "not_a_number"}
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert "not a valid integer" in str(serializer.errors)


def test_feature_value_serializer_rejects_invalid_boolean() -> None:
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
def test_serializer_rejects_nonexistent_segment(
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
def test_serializer_rejects_cross_project_segment(
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
