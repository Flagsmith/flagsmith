import pytest

from features.feature_states.serializers import (
    FeatureValueSerializer,
    UpdateFlagSerializer,
    UpdateFlagV2Serializer,
)
from features.models import Feature


def test_get_feature_raises_error_when_environment_not_in_context(
    feature: Feature,
) -> None:
    serializer = UpdateFlagSerializer(
        data={
            "feature": {"name": feature.name},
            "enabled": True,
            "value": {"type": "string", "string_value": "test"},
        },
        context={},  # No environment
    )
    serializer.is_valid()

    with pytest.raises(Exception) as exc_info:
        serializer.get_feature()

    assert "Environment context is required" in str(exc_info.value)


def test_validate_segment_overrides_returns_empty_list() -> None:
    serializer = UpdateFlagV2Serializer()
    result = serializer.validate_segment_overrides([])

    assert result == []


def test_feature_value_serializer_rejects_invalid_integer() -> None:
    serializer = FeatureValueSerializer(
        data={"type": "integer", "string_value": "not_a_number"}
    )

    assert serializer.is_valid() is False
    assert "not a valid integer" in str(serializer.errors)


def test_feature_value_serializer_rejects_invalid_boolean() -> None:
    serializer = FeatureValueSerializer(data={"type": "boolean", "string_value": "yes"})

    assert serializer.is_valid() is False
    assert "not a valid boolean" in str(serializer.errors)
