import re
from decimal import Decimal
from typing import Any, Union, get_args

from pydantic import BeforeValidator
from pydantic.types import AllowInfNan, StrictBool, StringConstraints
from typing_extensions import Annotated, TypeGuard

from util.engine_models.identities.traits.constants import TRAIT_STRING_VALUE_MAX_LENGTH

_UnconstrainedContextValue = Union[None, int, float, bool, str]


def map_any_value_to_trait_value(value: Any) -> _UnconstrainedContextValue:
    """
    Try to coerce a value of arbitrary type to a trait value type.
    Union member-specific constraints, such as max string value length, are ignored here.
    Replicate behaviour from marshmallow/pydantic V1 for number-like strings.
    For decimals return an int in case of unset exponent.
    When in doubt, return string.

    Supposed to be used as a `pydantic.BeforeValidator`.
    """
    if _is_trait_value(value):
        if isinstance(value, str):
            return _map_string_value_to_trait_value(value)
        return value
    if isinstance(value, Decimal):
        if value.as_tuple().exponent:
            return float(str(value))
        return int(value)
    return str(value)


_int_pattern = re.compile(r"-?[0-9]+")
_float_pattern = re.compile(r"-?[0-9]+\.[0-9]+")


def _map_string_value_to_trait_value(value: str) -> _UnconstrainedContextValue:
    if _int_pattern.fullmatch(value):
        return int(value)
    if _float_pattern.fullmatch(value):
        return float(value)
    return value


def _is_trait_value(value: Any) -> TypeGuard[_UnconstrainedContextValue]:
    return isinstance(value, get_args(_UnconstrainedContextValue))


ContextValue = Annotated[
    Union[
        None,
        StrictBool,
        Annotated[float, AllowInfNan(False)],
        int,
        Annotated[str, StringConstraints(max_length=TRAIT_STRING_VALUE_MAX_LENGTH)],
    ],
    BeforeValidator(map_any_value_to_trait_value),
]

TraitValue = ContextValue
