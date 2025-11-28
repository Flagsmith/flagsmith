from unittest.mock import Mock

import pytest

from environments.models import Environment
from features.feature_states.serializers import (
    FeatureValueSerializer,
    UpdateFlagSerializer,
    UpdateFlagV2Serializer,
)
from features.models import Feature
from features.versioning.dataclasses import FlagChangeSet


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


def test_add_audit_fields_sets_api_key_for_non_user(
    environment: Environment,
    feature: Feature,
) -> None:
    # Create a mock API key user (not FFAdminUser)
    mock_api_key = Mock()
    mock_api_key.key = "test_api_key"
    mock_request = Mock()
    mock_request.user = mock_api_key

    serializer = UpdateFlagSerializer(
        data={
            "feature": {"name": feature.name},
            "enabled": True,
            "value": {"type": "string", "string_value": "test"},
        },
        context={"environment": environment, "request": mock_request},
    )
    serializer.is_valid()

    change_set = FlagChangeSet(
        enabled=True,
        feature_state_value="test",
        type_="string",
    )
    serializer._add_audit_fields(change_set)

    assert change_set.api_key == "test_api_key"
    assert change_set.user is None


def test_validate_segment_overrides_returns_empty_list() -> None:
    serializer = UpdateFlagV2Serializer()
    result = serializer.validate_segment_overrides([])

    assert result == []


def test_get_typed_value_raises_error_for_unsupported_type() -> None:
    serializer = FeatureValueSerializer()
    # Bypass validation by setting validated_data directly
    serializer._validated_data = {"type": "unsupported", "string_value": "test"}  # type: ignore[attr-defined]

    with pytest.raises(ValueError) as exc_info:
        serializer.get_typed_value()

    assert "Unsupported value type: unsupported" in str(exc_info.value)
