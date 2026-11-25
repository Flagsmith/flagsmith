from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProjectUsage:
    project_id: int
    api_call_count: int


@dataclass(frozen=True)
class ApiCallBreakdown:
    flags: int
    identities: int
    traits: int
    environment_documents: int


@dataclass(frozen=True)
class UsageSnapshot:
    timestamp: datetime
    seat_count: int
    api_call_total: int
    api_call_breakdown: ApiCallBreakdown
    project_count: int
    instance_version: str
    project_usage: list[ProjectUsage]
