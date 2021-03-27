# Feature State Value Types
from features.value_types import INTEGER, STRING, BOOLEAN


def get_value_type(value: str) -> str:
    """
    Given a string, determine what type of value is contained in the string.

    e.g. "12" -> "int", "12.34" -> "float", etc.
    """
    if is_integer(value):
        return INTEGER
    elif is_boolean(value):
        return BOOLEAN
    else:
        return STRING


def is_integer(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def is_boolean(value):
    return value in ("true", "True", "false", "False")


def get_integer_from_string(value):
    try:
        return int(value)
    except ValueError:
        return 0


def get_boolean_from_string(value):
    if value in ("false", "False"):
        return False
    else:
        return True
