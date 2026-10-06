from __future__ import annotations

import typing
from typing import Any

import structlog
from clickhouse_driver import Client
from clickhouse_driver.util.helpers import parse_url
from django.conf import settings
from django.core.cache import cache
from rest_framework import serializers

from experimentation.dataclasses import (
    ConversionBucket,
    ExposureBucket,
    ResultsAggregates,
    WarehouseEventNames,
    WarehouseEventStats,
)
from experimentation.results_query import (
    _EXPOSURES_CTE,
    ResultsQueryBuilder,
    exposure_window_params,
)
from experimentation.warehouses.clickhouse import (
    EVENT_NAMES_QUERY,
    EVENT_STATS_QUERY,
    build_event_names,
    build_event_stats,
    event_names_query_params,
)
from experimentation.warehouses.constants import EVENT_NAMES_CACHE_SECONDS
from experimentation.warehouses.exceptions import UnsupportedWarehouseOperation

if typing.TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from experimentation.dataclasses import MetricSpec
    from experimentation.models import WarehouseConnection
    from experimentation.types import ExposureGranularity

logger = structlog.get_logger("warehouse")

CLICKHOUSE_CONNECT_TIMEOUT_SECONDS = 5
CLICKHOUSE_QUERY_TIMEOUT_SECONDS = 30
CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS = 120


def _get_clickhouse_client(
    send_receive_timeout: int = CLICKHOUSE_QUERY_TIMEOUT_SECONDS,
) -> Client:
    """Build a clickhouse-driver client for the experimentation event store.

    The database is taken from the DSN path, so queries can reference the
    `events` table unqualified. Connect and query timeouts are bounded unless the
    DSN overrides them.
    """
    host, kwargs = parse_url(settings.EXPERIMENTATION_CLICKHOUSE_URL)
    kwargs.setdefault("connect_timeout", CLICKHOUSE_CONNECT_TIMEOUT_SECONDS)
    kwargs.setdefault("send_receive_timeout", send_receive_timeout)
    kwargs.setdefault("client_name", settings.CLICKHOUSE_CONNECTION_CLIENT_NAME)
    return Client(host, **kwargs)


def get_warehouse_event_stats(environment_key: str) -> WarehouseEventStats:
    """Return event counts recorded for `environment_key` in the warehouse."""
    client = _get_clickhouse_client()
    try:
        rows = client.execute(
            EVENT_STATS_QUERY,
            {"environment_key": environment_key},
        )
    finally:
        client.disconnect()
    return build_event_stats(rows)


EXPOSURE_BUCKETS_QUERY = (
    _EXPOSURES_CTE
    + """
SELECT
    quarantined,
    variant,
    {bucket_function}(first_exposure, 'UTC') AS bucket,
    count() AS first_exposed_identities
FROM exposures
GROUP BY quarantined, variant, bucket
ORDER BY bucket
"""
)

_EXPOSURE_BUCKET_FUNCTIONS: dict[str, str] = {
    "hour": "toStartOfHour",
    "day": "toStartOfDay",
}


def get_exposure_buckets(
    *,
    environment_key: str,
    feature_name: str,
    window_start: datetime,
    window_end: datetime,
    granularity: ExposureGranularity,
) -> list[ExposureBucket]:
    client = _get_clickhouse_client(
        send_receive_timeout=CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS,
    )
    try:
        rows = client.execute(
            EXPOSURE_BUCKETS_QUERY.format(
                bucket_function=_EXPOSURE_BUCKET_FUNCTIONS[granularity]
            ),
            exposure_window_params(
                environment_key=environment_key,
                feature_name=feature_name,
                window_start=window_start,
                window_end=window_end,
            ),
        )
    finally:
        client.disconnect()
    return [
        ExposureBucket(
            variant=variant,
            bucket=bucket,
            first_exposed_identities=int(first_exposed_identities),
            quarantined=bool(quarantined),
        )
        for quarantined, variant, bucket, first_exposed_identities in rows
    ]


def get_results_aggregates(
    *,
    environment_key: str,
    feature_name: str,
    window_start: datetime,
    window_end: datetime,
    specs: Sequence[MetricSpec],
    granularity: ExposureGranularity,
) -> ResultsAggregates:
    """Run the warehouse reads behind one results refresh: per-variant identity
    counts and sufficient statistics, exposure buckets, and per charted metric
    the buckets of first post-exposure conversions.

    Three separate reads, so events landing mid-run can leave the chart's last
    point a few identities off the table until the next refresh."""
    builder = ResultsQueryBuilder(specs)
    params = builder.params(
        environment_key=environment_key,
        feature_name=feature_name,
        window_start=window_start,
        window_end=window_end,
    )
    client = _get_clickhouse_client(
        send_receive_timeout=CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS,
    )
    try:
        rows, columns = client.execute(
            builder.build_query(), params, with_column_types=True
        )
        exposure_counts, metric_stats = builder.decode_rows(
            rows, [name for name, _type in columns]
        )

        conversion_buckets: dict[int, list[ConversionBucket]] = {}
        conversions_query = builder.build_conversions_query(
            bucket_function=_EXPOSURE_BUCKET_FUNCTIONS[granularity]
        )
        if conversions_query is not None:
            rows, columns = client.execute(
                conversions_query, params, with_column_types=True
            )
            conversion_buckets = builder.decode_conversion_rows(
                rows, [name for name, _type in columns]
            )
    finally:
        client.disconnect()

    return ResultsAggregates(
        specs=list(specs),
        exposure_counts=exposure_counts,
        metric_stats=metric_stats,
        granularity=granularity,
        exposure_buckets=get_exposure_buckets(
            environment_key=environment_key,
            feature_name=feature_name,
            window_start=window_start,
            window_end=window_end,
            granularity=granularity,
        ),
        conversion_buckets=conversion_buckets,
    )


class FlagsmithWarehouse:
    def validate_config(
        self,
        config: dict[str, Any],
        *,
        stored: dict[str, Any] | None = None,
    ) -> None:
        if config:
            raise serializers.ValidationError(
                {"config": "Flagsmith warehouse does not accept configuration."}
            )
        return None

    def validate_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        raise UnsupportedWarehouseOperation(
            "Flagsmith connections take no credentials."
        )

    def verify(self, connection: WarehouseConnection) -> None:
        raise UnsupportedWarehouseOperation("Flagsmith connections are not verified.")

    def describe_error(self, error: Exception) -> str:
        raise UnsupportedWarehouseOperation("Flagsmith connections are not verified.")

    def get_event_names(
        self,
        connection: WarehouseConnection,
        environment_key: str,
    ) -> WarehouseEventNames | None:
        if not settings.EXPERIMENTATION_CLICKHOUSE_URL:
            return None
        cache_key = f"experimentation:event_names:{environment_key}"
        cached = cache.get(cache_key)
        if isinstance(cached, WarehouseEventNames):
            return cached
        client = _get_clickhouse_client()
        try:
            rows = client.execute(
                EVENT_NAMES_QUERY,
                event_names_query_params(environment_key),
            )
        except Exception:
            logger.warning(
                "connection.event_names_failed",
                environment__key=environment_key,
                exc_info=True,
            )
            return None
        finally:
            client.disconnect()
        event_names = build_event_names(rows)
        cache.set(cache_key, event_names, EVENT_NAMES_CACHE_SECONDS)
        return event_names

    def get_event_stats(
        self,
        connection: WarehouseConnection,
        environment_key: str,
    ) -> WarehouseEventStats | None:
        if not settings.EXPERIMENTATION_CLICKHOUSE_URL:
            return None
        try:
            return get_warehouse_event_stats(environment_key)
        except Exception:
            return None

    def get_exposure_buckets(
        self,
        connection: WarehouseConnection,
        *,
        environment_key: str,
        feature_name: str,
        window_start: datetime,
        window_end: datetime,
        granularity: ExposureGranularity,
    ) -> list[ExposureBucket]:
        return get_exposure_buckets(
            environment_key=environment_key,
            feature_name=feature_name,
            window_start=window_start,
            window_end=window_end,
            granularity=granularity,
        )

    def get_results_aggregates(
        self,
        connection: WarehouseConnection,
        *,
        environment_key: str,
        feature_name: str,
        window_start: datetime,
        window_end: datetime,
        specs: Sequence[MetricSpec],
        granularity: ExposureGranularity,
    ) -> ResultsAggregates:
        return get_results_aggregates(
            environment_key=environment_key,
            feature_name=feature_name,
            window_start=window_start,
            window_end=window_end,
            specs=specs,
            granularity=granularity,
        )
