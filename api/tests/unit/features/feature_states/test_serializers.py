from features.feature_states.serializers import FeatureValueSerializer


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
