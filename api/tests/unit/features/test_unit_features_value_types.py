import pytest

from features.constants import MAX_32_BIT_INTEGER
from features.value_types import ValueType


@pytest.mark.parametrize(
    "value, expected_type",
    (
        ("1", ValueType.INTEGER),
        (f"{MAX_32_BIT_INTEGER + 1}", ValueType.STRING),
        (f"{-MAX_32_BIT_INTEGER - 1}", ValueType.STRING),
        ("a string", ValueType.STRING),
        ("True", ValueType.BOOLEAN),
        ("true", ValueType.BOOLEAN),
        ("False", ValueType.BOOLEAN),
        ("false", ValueType.BOOLEAN),
        ('{"some_other": "data_type"}', ValueType.STRING),
    ),
)
def test_value_type_from_string(value: str, expected_type: ValueType) -> None:
    assert ValueType.from_string(value) == expected_type
