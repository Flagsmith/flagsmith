# Feature State Value Types
import sys

from features.constants import MAX_32_BIT_INTEGER
from features.value_types import BOOLEAN, INTEGER, STRING


def get_value_type(value: str) -> str:
    """
    Given a string, determine what type of value is contained in the string.

    e.g. "12" -> "int", "12.34" -> "float", etc.
    """
    if is_32_bit_integer(value):
        return INTEGER
    elif is_boolean(value):
        return BOOLEAN
    else:
        return STRING


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
