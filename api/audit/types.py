from typing import Literal, TypedDict

ChangeType = Literal["CREATE", "UPDATE", "DELETE", "UNKNOWN"]


class AuditLogChangeDetail(TypedDict):
    field: str
    old: int | float | str | bool | None
    new: int | float | str | bool | None
