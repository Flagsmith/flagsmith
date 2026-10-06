import typing
from collections.abc import Callable
from typing import Any

from experimentation.dataclasses import (
    ConversionBucket,
    ExposureBucket,
    ResultsAggregates,
    WarehouseEventNames,
    WarehouseEventStats,
)
from experimentation.results_query import (
    ResultsQueryBuilder,
    exposure_window_params,
    exposures_cte,
)
from experimentation.warehouses.constants import EVENT_NAMES_LIMIT

if typing.TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from experimentation.dataclasses import MetricSpec
    from experimentation.types import ExposureGranularity
    from experimentation.warehouses.dialect import Dialect

QueryRunner = Callable[
    [str, dict[str, object]], tuple["Sequence[Sequence[Any]]", list[str]]
]


def event_names_query(dialect: "Dialect") -> str:
    return (
        "SELECT event FROM events "
        f"WHERE environment_key = {dialect.param('environment_key')} "
        f"GROUP BY event ORDER BY max(timestamp) DESC LIMIT {dialect.param('limit')}"
    )


def event_stats_query(dialect: "Dialect") -> str:
    return (
        f"SELECT {dialect.count_all()} AS total, "
        f"{dialect.count_distinct('event')} AS unique "
        f"FROM events WHERE environment_key = {dialect.param('environment_key')}"
    )


def event_names_query_params(environment_key: str) -> dict[str, str | int]:
    # Fetch one row past the limit so truncation is detectable.
    return {
        "environment_key": environment_key,
        "limit": EVENT_NAMES_LIMIT + 1,
    }


def build_event_names(rows: "Sequence[Sequence[Any]]") -> WarehouseEventNames:
    names = [event for (event,) in rows]
    return WarehouseEventNames(
        events=names[:EVENT_NAMES_LIMIT],
        is_truncated=len(names) > EVENT_NAMES_LIMIT,
    )


def build_event_stats(rows: "Sequence[Sequence[Any]]") -> WarehouseEventStats:
    total, unique = rows[0] if rows else (0, 0)
    return WarehouseEventStats(
        total_events_received=int(total),
        unique_events_count=int(unique),
    )


def exposure_buckets_query(
    dialect: "Dialect", granularity: "ExposureGranularity"
) -> str:
    return (
        exposures_cte(dialect)
        + f"""
SELECT
    quarantined,
    variant,
    {dialect.time_bucket("first_exposure", granularity)} AS bucket,
    {dialect.count_all()} AS first_exposed_identities
FROM exposures
GROUP BY quarantined, variant, bucket
ORDER BY bucket
"""
    )


def read_exposure_buckets(
    run_query: QueryRunner,
    dialect: "Dialect",
    *,
    environment_key: str,
    feature_name: str,
    window_start: "datetime",
    window_end: "datetime",
    granularity: "ExposureGranularity",
) -> list[ExposureBucket]:
    rows, _columns = run_query(
        exposure_buckets_query(dialect, granularity),
        exposure_window_params(
            environment_key=environment_key,
            feature_name=feature_name,
            window_start=window_start,
            window_end=window_end,
        ),
    )
    return [
        ExposureBucket(
            variant=variant,
            bucket=bucket,
            first_exposed_identities=int(first_exposed_identities),
            quarantined=bool(quarantined),
        )
        for quarantined, variant, bucket, first_exposed_identities in rows
    ]


def read_results_aggregates(
    run_query: QueryRunner,
    dialect: "Dialect",
    *,
    environment_key: str,
    feature_name: str,
    window_start: "datetime",
    window_end: "datetime",
    specs: "Sequence[MetricSpec]",
    granularity: "ExposureGranularity",
) -> ResultsAggregates:
    """Run the reads behind one results refresh: per-variant identity counts
    and sufficient statistics, per charted metric the buckets of first
    post-exposure conversions, then exposure buckets.

    Three separate reads, so events landing mid-run can leave the chart's last
    point a few identities off the table until the next refresh."""
    builder = ResultsQueryBuilder(specs, dialect)
    params = builder.params(
        environment_key=environment_key,
        feature_name=feature_name,
        window_start=window_start,
        window_end=window_end,
    )
    rows, columns = run_query(builder.build_query(), params)
    exposure_counts, metric_stats = builder.decode_rows(list(rows), columns)

    conversion_buckets: dict[int, list[ConversionBucket]] = {}
    conversions_query = builder.build_conversions_query(granularity=granularity)
    if conversions_query is not None:
        rows, columns = run_query(conversions_query, params)
        conversion_buckets = builder.decode_conversion_rows(rows, columns)

    return ResultsAggregates(
        specs=list(specs),
        exposure_counts=exposure_counts,
        metric_stats=metric_stats,
        granularity=granularity,
        exposure_buckets=read_exposure_buckets(
            run_query,
            dialect,
            environment_key=environment_key,
            feature_name=feature_name,
            window_start=window_start,
            window_end=window_end,
            granularity=granularity,
        ),
        conversion_buckets=conversion_buckets,
    )
