from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WarehouseEventStats:
    total_events_received: int
    unique_events_count: int


@dataclass(frozen=True)
class ExposureBucket:
    """One time bucket of an experiment's exposures for one variant: how many
    identities were first exposed in the bucket, and the variant's exposure
    extremes within it."""

    variant: str
    bucket: datetime
    new_units: int
    first_exposure: datetime
    last_exposure: datetime
