from __future__ import annotations

import typing
from contextlib import contextmanager
from typing import Any

import structlog
from clickhouse_driver import Client
from clickhouse_driver.util.helpers import parse_url
from django.conf import settings
from django.core.cache import cache
from rest_framework import serializers

from experimentation.dataclasses import (
    WarehouseEventNames,
    WarehouseEventStats,
)
from experimentation.warehouses.clickhouse import (
    EVENT_NAMES_QUERY,
    EVENT_STATS_QUERY,
    QueryRunner,
    build_event_names,
    build_event_stats,
    event_names_query_params,
    read_exposure_buckets,
    read_results_aggregates,
)
from experimentation.warehouses.constants import EVENT_NAMES_CACHE_SECONDS
from experimentation.warehouses.exceptions import UnsupportedWarehouseOperation

if typing.TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from datetime import datetime

    from experimentation.dataclasses import (
        ExposureBucket,
        MetricSpec,
        ResultsAggregates,
    )
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


@contextmanager
def _background_query_runner() -> Iterator[QueryRunner]:
    client = _get_clickhouse_client(
        send_receive_timeout=CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS,
    )

    def run_query(
        query: str, params: dict[str, object]
    ) -> tuple[Sequence[Sequence[Any]], list[str]]:
        rows, columns = client.execute(query, params, with_column_types=True)
        return rows, [name for name, _type in columns]

    try:
        yield run_query
    finally:
        client.disconnect()


def get_exposure_buckets(
    *,
    environment_key: str,
    feature_name: str,
    window_start: datetime,
    window_end: datetime,
    granularity: ExposureGranularity,
) -> list[ExposureBucket]:
    with _background_query_runner() as run_query:
        return read_exposure_buckets(
            run_query,
            environment_key=environment_key,
            feature_name=feature_name,
            window_start=window_start,
            window_end=window_end,
            granularity=granularity,
        )


def get_results_aggregates(
    *,
    environment_key: str,
    feature_name: str,
    window_start: datetime,
    window_end: datetime,
    specs: Sequence[MetricSpec],
    granularity: ExposureGranularity,
) -> ResultsAggregates:
    with _background_query_runner() as run_query:
        return read_results_aggregates(
            run_query,
            environment_key=environment_key,
            feature_name=feature_name,
            window_start=window_start,
            window_end=window_end,
            specs=specs,
            granularity=granularity,
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
