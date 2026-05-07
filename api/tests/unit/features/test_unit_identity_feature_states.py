from typing import Any
from unittest import mock

from features.serializers import CreateFeatureSerializer
from features.models import Feature, FeatureState


def test_create_feature_serializer__get_identity_feature_state__returns_state_from_context() -> None:
    # Given
    feature = mock.MagicMock(spec=Feature, id=1)
    feature_state = mock.MagicMock(spec=FeatureState, feature_id=1, enabled=True)

    with mock.patch("features.serializers.FeatureStateSerializerSmall") as MockSerializer:
        MockSerializer.return_value.data = {"enabled": True, "feature_state_value": "foo"}

        context: dict[str, Any] = {
            "identity_feature_states": {1: feature_state}
        }
        serializer = CreateFeatureSerializer(instance=feature, context=context)

        # When
        result = serializer.get_identity_feature_state(feature)

        # Then
        assert result == {"enabled": True, "feature_state_value": "foo"}
        MockSerializer.assert_called_once_with(instance=feature_state)


def test_create_feature_serializer__get_identity_feature_state__returns_none_if_no_state_in_context() -> None:
    # Given
    feature = mock.MagicMock(spec=Feature, id=1)

    context: dict[str, Any] = {
        "identity_feature_states": {}
    }
    serializer = CreateFeatureSerializer(instance=feature, context=context)

    # When
    result = serializer.get_identity_feature_state(feature)

    # Then
    assert result is None


def test_create_feature_serializer__get_identity_feature_state__returns_none_if_context_missing_key() -> None:
    # Given
    feature = mock.MagicMock(spec=Feature, id=1)

    context: dict[str, Any] = {}
    serializer = CreateFeatureSerializer(instance=feature, context=context)

    # When
    result = serializer.get_identity_feature_state(feature)

    # Then
    assert result is None
