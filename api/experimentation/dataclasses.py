from dataclasses import dataclass
from datetime import datetime

from experimentation.types import ExposureGranularity


@dataclass(frozen=True)
class WarehouseEventStats:
    total_events_received: int
    unique_events_count: int


@dataclass(frozen=True)
class ExposureBucket:
    variant: str
    bucket: datetime
    first_exposed_identities: int
    quarantined: bool = False


@dataclass(frozen=True)
class ExposuresTimeseriesPoint:
    bucket: str
    new_identities: dict[str, int]


@dataclass(frozen=True)
class ExposuresTimeseries:
    granularity: ExposureGranularity
    points: list[ExposuresTimeseriesPoint]


@dataclass(frozen=True)
class ExposuresSummary:
    excluded_identities: int
    timeseries: ExposuresTimeseries
