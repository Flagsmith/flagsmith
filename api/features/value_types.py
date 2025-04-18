import sys
from enum import Enum
from typing import Any, Union

from features.constants import MAX_32_BIT_INTEGER

INTEGER = "int"
STRING = "unicode"
BOOLEAN = "bool"
FLOAT = "float"
FEATURE_STATE_VALUE_TYPES = (
    (INTEGER, "Integer"),
    (STRING, "String"),
    (BOOLEAN, "Boolean"),
)


class ValueType(Enum):
    INTEGER = "int"
    STRING = "unicode"
    BOOLEAN = "bool"
    FLOAT = "float"

    @classmethod
    def from_string(cls, value: str) -> "ValueType":
        if is_32_bit_integer(value):
            return ValueType.INTEGER
        elif is_boolean(value):
            return ValueType.BOOLEAN
        else:
            return ValueType.STRING

    @classmethod
    def from_any(
        cls,
        value: Any,
        exclude_types: list["ValueType"] | None = None,
        default: Union["ValueType", None] = None,
    ) -> "ValueType":
        exclude_types = exclude_types or []
        default = default or ValueType.STRING

        try:
            raw_type = type(value).__name__
            value_type = ValueType(raw_type)
            if value_type in exclude_types:
                return default
            return value_type
        except ValueError:
            return default


def is_32_bit_integer(value: str) -> bool:
    return is_integer(value, max_abs_value=MAX_32_BIT_INTEGER)


def is_integer(value: str, max_abs_value: int = sys.maxsize) -> bool:
    try:
        int_value = int(value)
        return abs(int_value) < max_abs_value
    except ValueError:
        return False


def is_boolean(value: str) -> bool:
    return value in ("true", "True", "false", "False")


def get_integer_from_string(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def get_boolean_from_string(value: str) -> bool:
    if value in ("false", "False"):
        return False
    else:
        return True
