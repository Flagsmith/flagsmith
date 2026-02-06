import pytest

from util.engine_models.identities.traits.types import (
    map_any_value_to_trait_value,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        # String values that look like integers should be converted to int
        ("123", 123),
        ("-45", -45),
        ("0", 0),
        # String values that look like floats should be converted to float
        ("1.23", 1.23),
        ("-4.56", -4.56),
        ("0.0", 0.0),
        # Non-trait-value types should be converted to string
        (["a", "list"], "['a', 'list']"),
        ({"a": "dict"}, "{'a': 'dict'}"),
    ],
)
def test_map_any_value_to_trait_value(value: object, expected: object) -> None:
    # When
    result = map_any_value_to_trait_value(value)

    # Then
    assert result == expected
