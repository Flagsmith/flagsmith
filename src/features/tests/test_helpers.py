import pytest

from features.helpers import get_correctly_typed_value
from features.utils import INTEGER, BOOLEAN, STRING


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
