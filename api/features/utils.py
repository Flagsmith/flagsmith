# Feature State Value Types
import typing

from features.value_types import BOOLEAN, INTEGER, STRING

MAX_INTEGER_SIZE = 2147483647
MIN_INTEGER_SIZE = -MAX_INTEGER_SIZE


def get_value_type(
    value: str,
    max_integer_size: int = MAX_INTEGER_SIZE,
    min_integer_size: int = MIN_INTEGER_SIZE,
) -> str:
    """
    Given a string, determine what type of value is contained in the string.

    e.g. "12" -> "int", "12.34" -> "float", etc.
    """
    if _is_integer(value, max_size=max_integer_size, min_size=min_integer_size):
        return INTEGER
    elif _is_boolean(value):
        return BOOLEAN

    return STRING


def _is_integer(value: typing.Any, max_size: int, min_size: int):
    try:
        return min_size <= int(value) <= max_size
    except ValueError:
        return False


def _is_boolean(value):
    return value in ("true", "True", "false", "False")


def get_integer_from_string(value):
    try:
        return int(value)
    except ValueError:
        return 0


def get_boolean_from_string(value):
    return value not in ("false", "False")
