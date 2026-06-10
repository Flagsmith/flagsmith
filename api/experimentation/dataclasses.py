from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WarehouseEventStats:
    total_events_received: int
    unique_events_count: int


@dataclass(frozen=True)
class ExposureBucket:
    """Identities are bucketed by first exposure, so ``last_exposure`` may
    fall outside the bucket."""

    variant: str
    bucket: datetime
    first_exposed_identities: int
    first_exposure: datetime
    last_exposure: datetime
