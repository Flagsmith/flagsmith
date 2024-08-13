import typing

from typing_extensions import NotRequired


class SDKTraitValueData(typing.TypedDict):
    type: str
    value: str


class SDKTraitData(typing.TypedDict):
    trait_key: str
    trait_value: SDKTraitValueData
    transient: NotRequired[bool]
