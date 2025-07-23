from typing import Any, NotRequired, Protocol, TypedDict


class _HasId(Protocol):
    id: int


class MetadataItem(TypedDict):
    model_field: _HasId
    field_value: Any
    delete: NotRequired[bool]
