from dataclasses import dataclass


@dataclass(frozen=True)
class WarehouseEventStats:
    total_events_received: int
    unique_events_count: int
