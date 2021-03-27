import pytest

from features.utils import get_value_type
from features.value_types import INTEGER, STRING, BOOLEAN


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
