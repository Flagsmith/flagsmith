from typing import Literal, TypedDict

ChangeType = Literal["CREATE", "UPDATE", "DELETE", "UNKNOWN"]


class AuditLogChangeDetail(TypedDict):
    field: str
    old: int | float | str | bool | None
    new: int | float | str | bool | None


class AuditLogsQueryParams(TypedDict, total=False):
    organisation: int
    project: int
    environments: list[int]
    is_system_event: bool | None
    is_organisation_level: bool | None
    search: str
