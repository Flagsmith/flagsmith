import pytest
from django.core.cache import cache

from experimentation.dataclasses import WarehouseEventNames, WarehouseEventStats
from experimentation.warehouses.cache import cache_warehouse_read_unless_empty


@pytest.mark.parametrize(
    "result, expected_cached",
    [
        (WarehouseEventNames(events=[], is_truncated=False), False),
        (WarehouseEventNames(events=["purchase"], is_truncated=False), True),
        (WarehouseEventStats(total_events_received=0, unique_events_count=0), False),
        (WarehouseEventStats(total_events_received=3, unique_events_count=2), True),
    ],
    ids=["empty_names", "names", "zero_stats", "stats"],
)
def test_cache_warehouse_read_unless_empty__empty_or_populated_result__caches_only_populated(
    db: None,
    reset_cache: None,
    result: WarehouseEventNames | WarehouseEventStats,
    expected_cached: bool,
) -> None:
    # When
    cache_warehouse_read_unless_empty("key", result, 60)

    # Then
    assert (cache.get("key") == result) is expected_cached
