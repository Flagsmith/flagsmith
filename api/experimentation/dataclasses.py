from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WarehouseEventStats:
    total_events_received: int
    unique_events_count: int


@dataclass(frozen=True)
class ExposureBucket:
    variant: str
    bucket: datetime
    first_exposed_identities: int
