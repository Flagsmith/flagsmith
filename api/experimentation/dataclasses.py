from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WarehouseEventStats:
    total_events_received: int
    unique_events_count: int


@dataclass(frozen=True)
class ExposureBucket:
    """One exposures-query row: variant × time bucket.

    Identities count once, in the bucket of their first exposure — so
    ``first_exposed_identities`` sums without double counting.
    ``last_exposure`` is the latest of *any* exposure, not just first ones.
    """

    variant: str
    bucket: datetime
    first_exposed_identities: int
    first_exposure: datetime
    last_exposure: datetime
