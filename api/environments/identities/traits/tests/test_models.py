import pytest

from environments.identities.traits.models import Trait


@pytest.mark.parametrize(
    "value, expected_data",
    (
        (1, {"value_type": "int", "integer_value": 1}),
        (0, {"value_type": "int", "integer_value": 0}),
        ("my_string", {"value_type": "unicode", "string_value": "my_string"}),
        (True, {"value_type": "bool", "boolean_value": True}),
        (False, {"value_type": "bool", "boolean_value": False}),
        (123.4, {"value_type": "float", "float_value": 123.4}),
    ),
)
def test_generate_trait_value_data_for_value(value, expected_data):
    assert Trait.generate_trait_value_data(value) == expected_data


@pytest.mark.parametrize(
    "deserialized_data, expected_data",
    (
        ({"type": "int", "value": 1}, {"value_type": "int", "integer_value": 1}),
        ({"type": "int", "value": 0}, {"value_type": "int", "integer_value": 0}),
        (
            {"type": "unicode", "value": "my_string"},
            {"value_type": "unicode", "string_value": "my_string"},
        ),
        (
            {"type": "bool", "value": True},
            {"value_type": "bool", "boolean_value": True},
        ),
        (
            {"type": "bool", "value": False},
            {"value_type": "bool", "boolean_value": False},
        ),
        (
            {"type": "float", "value": 123.4},
            {"value_type": "float", "float_value": 123.4},
        ),
    ),
)
def test_generate_trait_value_data_for_deserialized_data(
    deserialized_data, expected_data
):
    assert Trait.generate_trait_value_data(deserialized_data) == expected_data
