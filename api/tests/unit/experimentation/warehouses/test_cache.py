import pytest
from django.core.cache import cache

from experimentation.dataclasses import WarehouseEventNames, WarehouseEventStats
from experimentation.warehouses.cache import cache_warehouse_read_unless_empty


@pytest.mark.parametrize(
    "warehouse_read, expected_cached",
    [
        (WarehouseEventNames(events=[], is_truncated=False), False),
        (WarehouseEventStats(total_events_received=0, unique_events_count=0), False),
        (WarehouseEventStats(total_events_received=3, unique_events_count=2), True),
    ],
    ids=["empty_names", "zero_stats", "populated_stats"],
)
def test_cache_warehouse_read_unless_empty__empty_or_populated_read__caches_only_non_empty_read(
    db: None,
    reset_cache: None,
    warehouse_read: WarehouseEventNames | WarehouseEventStats,
    expected_cached: bool,
) -> None:
    # When
    cache_warehouse_read_unless_empty("key", warehouse_read, 60)

    # Then
    assert (cache.get("key") == warehouse_read) is expected_cached
