import typing

from typing_extensions import NotRequired


class SDKTraitValueData(typing.TypedDict):
    type: str
    value: str | int | bool | float


# Trait value can be either:
# 1. A structured SDKTraitValueData (from serializer validation via TraitValueField)
# 2. A raw primitive value (str, int, bool, float) when called directly
# 3. None (to delete the trait)
TraitValue: typing.TypeAlias = SDKTraitValueData | str | int | bool | float | None


class SDKTraitData(typing.TypedDict):
    trait_key: str
    trait_value: TraitValue
    transient: NotRequired[bool]
