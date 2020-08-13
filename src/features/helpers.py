import typing

from features.utils import INTEGER, BOOLEAN


def get_correctly_typed_value(value_type: str, string_value: str) -> typing.Any:
    if value_type == INTEGER:
        return int(string_value)
    elif value_type == BOOLEAN:
        return string_value == 'True'

    return string_value

