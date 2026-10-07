import typing
from collections.abc import Callable
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

import clickhouse_connect
import structlog
from clickhouse_connect.driver import httputil
from clickhouse_connect.driver.exceptions import (
    DatabaseError,
    OperationalError,
)
from django.core.cache import cache
from rest_framework import serializers
from urllib3 import PoolManager

from core.network import is_internal_address
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
from experimentation.types import (
    CLICKHOUSE_DEFAULTS,
    ClickHouseConfig,
    ClickHouseCredentials,
)
from experimentation.warehouses.cache import (
    CUSTOMER_EVENT_UNAVAILABLE,
    customer_cache_key,
)
from experimentation.warehouses.constants import (
    CUSTOMER_EVENT_NAMES_FAILURE_CACHE_SECONDS,
    CUSTOMER_EVENT_STATS_CACHE_SECONDS,
    EVENT_NAMES_CACHE_SECONDS,
    EVENT_NAMES_LIMIT,
)
from experimentation.warehouses.exceptions import (
    DeliveryConfigError,
    MissingEventsTableError,
)

if typing.TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from datetime import datetime

    from clickhouse_connect.driver.client import Client

    from experimentation.dataclasses import MetricSpec
    from experimentation.models import WarehouseConnection
    from experimentation.types import ExposureGranularity

EVENTS_TABLE_NAME = "events"

CONNECT_TIMEOUT_SECONDS = 10


class _NoRedirectPoolManager(PoolManager):
    """The internal-address guard validates the host we dial; following a
    redirect would let a permitted host bounce the request, and its event
    payload, to an address that was never checked."""

    def urlopen(  # type: ignore[override]
        self,
        method: str,
        url: str,
        redirect: bool = True,
        **kwargs: "Any",
    ) -> "Any":
        kwargs["redirect"] = False
        return super().urlopen(method, url, **kwargs)


@lru_cache(maxsize=1)
def _get_pool_manager() -> PoolManager:
    # Shared across delivery clients, as clickhouse-connect's own default pool
    # is: the manager pools connections per host and is thread-safe.
    return _NoRedirectPoolManager(**httputil.get_pool_manager_options())


MISSING_EVENTS_TABLE_DETAIL = (
    "Events table not found in the configured database. Run the setup SQL to create it."
)


def describe_warehouse_error(error: Exception) -> str:
    """Return a user-facing description of a failed verification, suitable for
    the connection's ``status_detail``. Raw exception text stays in the logs:
    it can carry internal infrastructure details."""
    if isinstance(error, DeliveryConfigError):
        return str(error)
    # OperationalError subclasses DatabaseError, so it is matched first.
    if isinstance(error, OperationalError):
        return "Could not connect to the host."
    if isinstance(error, DatabaseError):
        # 516/194 = AUTHENTICATION_FAILED/REQUIRED_PASSWORD, 81 = UNKNOWN_DATABASE, 60 = UNKNOWN_TABLE
        if error.code in (516, 194):
            return "Authentication failed."
        if error.code == 81:
            return "Database does not exist."
        if error.code == 60:
            return MISSING_EVENTS_TABLE_DETAIL
        return "The ClickHouse server rejected the request."
    if isinstance(error, MissingEventsTableError):
        return MISSING_EVENTS_TABLE_DETAIL
    return "Connection failed."


@contextmanager
def delivery_client(
    connection: "WarehouseConnection",
    *,
    send_receive_timeout: int,
) -> "Iterator[Client]":
    """Yield a ClickHouse HTTP client for a connection, over the same interface
    and port events are delivered on, so a connection that verifies is one that
    delivery can use.

    Raises ``DeliveryConfigError`` if the stored configuration cannot be turned
    into a usable client.
    """
    config = typing.cast(ClickHouseConfig, connection.config or {})
    credentials = typing.cast(ClickHouseCredentials, connection.credentials or {})
    try:
        host = config["host"]
        port = config["port"]
        database = config["database"]
        username = config["username"]
        secure = config["secure"]
        password = credentials["password"]
    except KeyError as exc:
        raise DeliveryConfigError("Stored connection details are incomplete.") from exc

    # Re-checked immediately before connecting: DNS may resolve differently
    # than it did at validation time.
    if is_internal_address(host, include_shared=True):
        raise DeliveryConfigError(
            "Host must not target internal or private network addresses."
        )

    client = clickhouse_connect.get_client(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        secure=secure,
        connect_timeout=CONNECT_TIMEOUT_SECONDS,
        send_receive_timeout=send_receive_timeout,
        pool_mgr=_get_pool_manager(),
    )
    try:
        yield client
    finally:
        client.close()


def check_events_table_exists(client: "Client") -> None:
    """Raise ``MissingEventsTableError`` if the connection's database has no
    events table for delivery to insert into."""
    rows = client.query(f"EXISTS TABLE {EVENTS_TABLE_NAME}").result_rows
    if not rows[0][0]:
        raise MissingEventsTableError()


logger = structlog.get_logger("warehouse")

VERIFY_TIMEOUT_SECONDS = 5
EVENT_NAMES_TIMEOUT_SECONDS = 15
BACKGROUND_QUERY_TIMEOUT_SECONDS = 120

# Pinned so a customer's settings profile cannot change what results compute.
RESULTS_QUERY_SETTINGS = {
    "join_use_nulls": 0,
    "aggregate_functions_null_for_empty": 0,
}

EVENT_NAMES_QUERY = (
    "SELECT event FROM events "
    "WHERE environment_key = %(environment_key)s "
    "GROUP BY event ORDER BY max(timestamp) DESC LIMIT %(limit)s"
)
EVENT_STATS_QUERY = (
    "SELECT count() AS total, uniqExact(event) AS unique "
    "FROM events WHERE environment_key = %(environment_key)s"
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


QueryRunner = Callable[
    [str, dict[str, object]], tuple["Sequence[Sequence[Any]]", list[str]]
]

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

EXPOSURE_BUCKET_FUNCTIONS: dict[str, str] = {
    "hour": "toStartOfHour",
    "day": "toStartOfDay",
}


def read_exposure_buckets(
    run_query: QueryRunner,
    *,
    environment_key: str,
    feature_name: str,
    window_start: "datetime",
    window_end: "datetime",
    granularity: "ExposureGranularity",
) -> list[ExposureBucket]:
    rows, _columns = run_query(
        EXPOSURE_BUCKETS_QUERY.format(
            bucket_function=EXPOSURE_BUCKET_FUNCTIONS[granularity]
        ),
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
    builder = ResultsQueryBuilder(specs)
    params = builder.params(
        environment_key=environment_key,
        feature_name=feature_name,
        window_start=window_start,
        window_end=window_end,
    )
    rows, columns = run_query(builder.build_query(), params)
    exposure_counts, metric_stats = builder.decode_rows(list(rows), columns)

    conversion_buckets: dict[int, list[ConversionBucket]] = {}
    conversions_query = builder.build_conversions_query(
        bucket_function=EXPOSURE_BUCKET_FUNCTIONS[granularity]
    )
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
            environment_key=environment_key,
            feature_name=feature_name,
            window_start=window_start,
            window_end=window_end,
            granularity=granularity,
        ),
        conversion_buckets=conversion_buckets,
    )


def _customer_query_runner(client: "Client") -> QueryRunner:
    def run_query(
        query: str, params: dict[str, object]
    ) -> "tuple[Sequence[Sequence[Any]], list[str]]":
        # "aware" keeps UTC on bucket datetimes so charts serialise with an offset.
        result = client.query(
            query,
            parameters=params,
            settings=RESULTS_QUERY_SETTINGS,
            tz_mode="aware",
        )
        return result.result_rows, list(result.column_names)

    return run_query


class ClickHouseWarehouse:
    def validate_config(
        self,
        config: dict[str, Any],
        *,
        stored: dict[str, Any] | None = None,
    ) -> ClickHouseConfig:
        if not isinstance(config, dict):
            raise serializers.ValidationError({"config": "Must be an object."})
        if unknown_keys := set(config) - set(CLICKHOUSE_DEFAULTS):
            raise serializers.ValidationError(
                {"config": {key: "Unknown field." for key in sorted(unknown_keys)}}
            )
        base = stored if stored is not None else dict(CLICKHOUSE_DEFAULTS)
        merged: dict[str, Any] = {**base, **config}
        if not merged["host"] or not isinstance(merged["host"], str):
            raise serializers.ValidationError(
                {"config": {"host": "This field is required."}}
            )
        if is_internal_address(merged["host"], include_shared=True):
            raise serializers.ValidationError(
                {
                    "config": {
                        "host": (
                            "Host must not target internal or private network addresses."
                        )
                    }
                }
            )
        port = merged["port"]
        if (
            isinstance(port, bool)
            or not isinstance(port, int)
            or not (1 <= port <= 65535)
        ):
            raise serializers.ValidationError(
                {"config": {"port": "Enter a valid port number (1-65535)."}}
            )
        for key in ("database", "username"):
            if not merged[key] or not isinstance(merged[key], str):
                raise serializers.ValidationError(
                    {"config": {key: "Must be a non-empty string."}}
                )
        if not isinstance(merged["secure"], bool):
            raise serializers.ValidationError(
                {"config": {"secure": "Must be a boolean."}}
            )
        return typing.cast(ClickHouseConfig, merged)

    def validate_credentials(
        self, credentials: dict[str, Any]
    ) -> ClickHouseCredentials:
        if not isinstance(credentials, dict):
            raise serializers.ValidationError({"credentials": "Must be an object."})
        password = credentials.get("password")
        if not password or not isinstance(password, str):
            raise serializers.ValidationError(
                {"credentials": {"password": "This field is required."}}
            )
        return {"password": password}

    def verify(self, connection: "WarehouseConnection") -> None:
        with delivery_client(
            connection,
            send_receive_timeout=VERIFY_TIMEOUT_SECONDS,
        ) as client:
            check_events_table_exists(client)

    def describe_error(self, error: Exception) -> str:
        return describe_warehouse_error(error)

    def get_event_names(
        self,
        connection: "WarehouseConnection",
        environment_key: str,
    ) -> WarehouseEventNames | None:
        cache_key = customer_cache_key("event_names", connection)
        cached = cache.get(cache_key)
        if isinstance(cached, WarehouseEventNames):
            return cached
        if cached == CUSTOMER_EVENT_UNAVAILABLE:
            return None
        try:
            with delivery_client(
                connection,
                send_receive_timeout=EVENT_NAMES_TIMEOUT_SECONDS,
            ) as client:
                rows = client.query(
                    EVENT_NAMES_QUERY,
                    parameters=event_names_query_params(environment_key),
                ).result_rows
        except Exception:
            cache.set(
                cache_key,
                CUSTOMER_EVENT_UNAVAILABLE,
                CUSTOMER_EVENT_NAMES_FAILURE_CACHE_SECONDS,
            )
            logger.warning(
                "connection.event_names_failed",
                environment__id=connection.environment_id,
                exc_info=True,
            )
            return None
        event_names = build_event_names(rows)
        cache.set(cache_key, event_names, EVENT_NAMES_CACHE_SECONDS)
        return event_names

    def get_event_stats(
        self,
        connection: "WarehouseConnection",
        environment_key: str,
    ) -> WarehouseEventStats | None:
        cache_key = customer_cache_key("event_stats", connection)
        cached = cache.get(cache_key)
        if isinstance(cached, WarehouseEventStats):
            return cached
        if cached == CUSTOMER_EVENT_UNAVAILABLE:
            return None
        try:
            with delivery_client(
                connection,
                send_receive_timeout=VERIFY_TIMEOUT_SECONDS,
            ) as client:
                rows = client.query(
                    EVENT_STATS_QUERY,
                    parameters={"environment_key": environment_key},
                ).result_rows
            stats = build_event_stats(rows)
        except Exception:
            cache.set(
                cache_key,
                CUSTOMER_EVENT_UNAVAILABLE,
                CUSTOMER_EVENT_STATS_CACHE_SECONDS,
            )
            logger.warning(
                "connection.event_stats_failed",
                environment__id=connection.environment_id,
                exc_info=True,
            )
            return None
        cache.set(cache_key, stats, CUSTOMER_EVENT_STATS_CACHE_SECONDS)
        return stats

    def get_exposure_buckets(
        self,
        connection: "WarehouseConnection",
        *,
        environment_key: str,
        feature_name: str,
        window_start: "datetime",
        window_end: "datetime",
        granularity: "ExposureGranularity",
    ) -> list[ExposureBucket]:
        with delivery_client(
            connection,
            send_receive_timeout=BACKGROUND_QUERY_TIMEOUT_SECONDS,
        ) as client:
            return read_exposure_buckets(
                _customer_query_runner(client),
                environment_key=environment_key,
                feature_name=feature_name,
                window_start=window_start,
                window_end=window_end,
                granularity=granularity,
            )

    def get_results_aggregates(
        self,
        connection: "WarehouseConnection",
        *,
        environment_key: str,
        feature_name: str,
        window_start: "datetime",
        window_end: "datetime",
        specs: "Sequence[MetricSpec]",
        granularity: "ExposureGranularity",
    ) -> ResultsAggregates:
        with delivery_client(
            connection,
            send_receive_timeout=BACKGROUND_QUERY_TIMEOUT_SECONDS,
        ) as client:
            return read_results_aggregates(
                _customer_query_runner(client),
                environment_key=environment_key,
                feature_name=feature_name,
                window_start=window_start,
                window_end=window_end,
                specs=specs,
                granularity=granularity,
            )
