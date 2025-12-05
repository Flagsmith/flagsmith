from environments.sdk.services import get_transient_identifier
from environments.sdk.types import SDKTraitData


class TestGetTransientIdentifier:
    def test_returns_consistent_hash_for_structured_trait_value(self) -> None:
        """Test with SDKTraitValueData format (from serializer validation)."""
        sdk_trait_data: list[SDKTraitData] = [
            {
                "trait_key": "key1",
                "trait_value": {"type": "str", "value": "value1"},
            }
        ]

        result1 = get_transient_identifier(sdk_trait_data)
        result2 = get_transient_identifier(sdk_trait_data)

        assert result1 == result2
        assert len(result1) == 64  # SHA256 hex digest length

    def test_returns_consistent_hash_for_raw_primitive_string(self) -> None:
        """Test with raw string value (direct call without serializer)."""
        sdk_trait_data: list[SDKTraitData] = [
            {
                "trait_key": "key1",
                "trait_value": "value1",
            }
        ]

        result1 = get_transient_identifier(sdk_trait_data)
        result2 = get_transient_identifier(sdk_trait_data)

        assert result1 == result2
        assert len(result1) == 64

    def test_returns_consistent_hash_for_raw_primitive_int(self) -> None:
        """Test with raw int value."""
        sdk_trait_data: list[SDKTraitData] = [
            {
                "trait_key": "key1",
                "trait_value": 42,
            }
        ]

        result1 = get_transient_identifier(sdk_trait_data)
        result2 = get_transient_identifier(sdk_trait_data)

        assert result1 == result2
        assert len(result1) == 64

    def test_returns_consistent_hash_for_raw_primitive_bool(self) -> None:
        """Test with raw bool value."""
        sdk_trait_data: list[SDKTraitData] = [
            {
                "trait_key": "key1",
                "trait_value": True,
            }
        ]

        result1 = get_transient_identifier(sdk_trait_data)
        result2 = get_transient_identifier(sdk_trait_data)

        assert result1 == result2
        assert len(result1) == 64

    def test_returns_consistent_hash_for_raw_primitive_float(self) -> None:
        """Test with raw float value."""
        sdk_trait_data: list[SDKTraitData] = [
            {
                "trait_key": "key1",
                "trait_value": 3.14,
            }
        ]

        result1 = get_transient_identifier(sdk_trait_data)
        result2 = get_transient_identifier(sdk_trait_data)

        assert result1 == result2
        assert len(result1) == 64

    def test_returns_different_hash_for_different_values(self) -> None:
        """Test that different values produce different hashes."""
        sdk_trait_data_1: list[SDKTraitData] = [
            {"trait_key": "key1", "trait_value": "value1"}
        ]
        sdk_trait_data_2: list[SDKTraitData] = [
            {"trait_key": "key1", "trait_value": "value2"}
        ]

        result1 = get_transient_identifier(sdk_trait_data_1)
        result2 = get_transient_identifier(sdk_trait_data_2)

        assert result1 != result2

    def test_skips_none_trait_values(self) -> None:
        """Test that None values are skipped."""
        sdk_trait_data: list[SDKTraitData] = [
            {"trait_key": "key1", "trait_value": "value1"},
            {"trait_key": "key2", "trait_value": None},
        ]

        # Should not raise and should only use non-None values
        result = get_transient_identifier(sdk_trait_data)
        assert len(result) == 64

    def test_returns_uuid_for_empty_list(self) -> None:
        """Test that empty list returns a UUID."""
        result = get_transient_identifier([])

        # UUID hex is 32 characters
        assert len(result) == 32

    def test_structured_and_raw_same_value_produce_same_hash(self) -> None:
        """Test that structured SDKTraitValueData and raw value with same content produce same hash."""
        structured: list[SDKTraitData] = [
            {"trait_key": "key1", "trait_value": {"type": "str", "value": "test"}}
        ]
        raw: list[SDKTraitData] = [{"trait_key": "key1", "trait_value": "test"}]

        result_structured = get_transient_identifier(structured)
        result_raw = get_transient_identifier(raw)

        assert result_structured == result_raw
