from typing import Literal, Protocol, TypedDict

ChangeType = Literal["CREATE", "UPDATE", "DELETE", "UNKNOWN"]


class AxesLoginRequest(Protocol):
    axes_failures_since_start: int


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
