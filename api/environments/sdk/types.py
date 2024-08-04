import typing

from typing_extensions import NotRequired


class SDKTraitData(typing.TypedDict):
    trait_key: str
    trait_value: typing.Any
    transient: NotRequired[bool]
