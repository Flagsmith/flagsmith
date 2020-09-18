import pytest

from features.feature_states.helpers import get_correctly_typed_value, get_value_type
from features.constants import INTEGER, BOOLEAN, STRING


@pytest.mark.parametrize(
    "value_type, string_value, expected_value",
    (
        (INTEGER, "123", 123),
        (BOOLEAN, "True", True),
        (BOOLEAN, "False", False),
        (STRING, "my_string", "my_string"),
        (STRING, "True", "True"),
        (STRING, "False", "False"),
    ),
)
def test_get_correctly_typed_value(value_type, string_value, expected_value):
    assert get_correctly_typed_value(value_type, string_value) == expected_value


@pytest.mark.parametrize(
    "value, expected_type",
    (
        ("1", INTEGER),
        ("a string", STRING),
        ("True", BOOLEAN),
        ("true", BOOLEAN),
        ("False", BOOLEAN),
        ("false", BOOLEAN),
        ('{"some_other": "data_type"}', STRING),
    ),
)
def test_get_value_type(value, expected_type):
    assert get_value_type(value) == expected_type
