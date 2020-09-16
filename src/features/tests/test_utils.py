import pytest

from features.utils import get_value_type, INTEGER, FLOAT, STRING, BOOLEAN


@pytest.mark.parametrize("value, expected_type", (
        ("1", INTEGER),
        ("12.34", FLOAT),
        ("a string", STRING),
        ("True", BOOLEAN),
        ("true", BOOLEAN),
        ("False", BOOLEAN),
        ("false", BOOLEAN),
        ("{\"some_other\": \"data_type\"}", STRING)
))
def test_get_value_type(value, expected_type):
    assert get_value_type(value) == expected_type
