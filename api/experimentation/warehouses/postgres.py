import ipaddress
import re
import typing
from contextlib import closing, contextmanager
from typing import Any

import psycopg2
import structlog
from common.core.utils import is_saas
from django.core.cache import cache
from django.db import DEFAULT_DB_ALIAS, connections
from psycopg2 import sql
from rest_framework import serializers

from experimentation.dataclasses import (
    ExposureBucket,
    ResultsAggregates,
    WarehouseEventNames,
    WarehouseEventStats,
)
from experimentation.types import (
    POSTGRES_DEFAULTS,
    PostgresConfig,
    PostgresCredentials,
)
from experimentation.warehouses.base import is_disallowed_host
from experimentation.warehouses.cache import (
    CUSTOMER_EVENT_UNAVAILABLE,
    customer_cache_key,
)
from experimentation.warehouses.constants import (
    BACKGROUND_QUERY_TIMEOUT_SECONDS,
    CUSTOMER_EVENT_NAMES_FAILURE_CACHE_SECONDS,
    CUSTOMER_EVENT_STATS_CACHE_SECONDS,
    EVENT_NAMES_CACHE_SECONDS,
    EVENT_NAMES_TIMEOUT_SECONDS,
    FLAGSMITH_DATABASE_MISSING_EVENTS_TABLE_DETAIL,
    FLAGSMITH_DATABASE_PERMISSION_DENIED_DETAIL,
    FLAGSMITH_DATABASE_SCHEMA,
    FLAGSMITH_DATABASE_SOURCE,
    FLAGSMITH_DATABASE_UNAVAILABLE_DETAIL,
    MISSING_EVENTS_TABLE_DETAIL,
    PERMISSION_DENIED_DETAIL,
    QUERY_TIMEOUT_DETAIL,
    SCHEMA_MISMATCH_DETAIL,
    VERIFY_TIMEOUT_SECONDS,
)
from experimentation.warehouses.dialect import POSTGRES_DIALECT
from experimentation.warehouses.exceptions import (
    DeliveryConfigError,
    EventsTablePermissionError,
    EventsTableSchemaMismatchError,
    MissingEventsTableError,
)
from experimentation.warehouses.queries import (
    QueryResult,
    QueryRunner,
    build_event_names,
    build_event_stats,
    event_names_query,
    event_names_query_params,
    event_stats_query,
    read_exposure_buckets,
    read_results_aggregates,
)

if typing.TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from datetime import datetime

    from psycopg2.extensions import cursor as Cursor

    from experimentation.dataclasses import MetricSpec
    from experimentation.models import WarehouseConnection
    from experimentation.types import ExposureGranularity

logger = structlog.get_logger("warehouse")

CONNECT_TIMEOUT_SECONDS = 10

# Kept in step with experimentation/postgres/events.sql.
EVENTS_TABLE_COLUMN_TYPES = {
    "environment_key": "text",
    "event": "text",
    "feature_name": "text",
    "timestamp": "timestamp with time zone",
    "collected_at": "timestamp with time zone",
    "identifier": "text",
    "value": "text",
    "traits": "text",
    "metadata": "text",
    "sdk_language": "text",
    "sdk_version": "text",
}

# One hostname, IPv4 or IPv6 address: libpq would also accept a host list or a
# socket directory, either of which would sidestep the internal-address check.
HOST_PATTERN = re.compile(
    r"(?!-)[A-Za-z0-9_-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9_-]{1,63}(?<!-))*"
)
# Lowercase only: the setup SQL leaves it unquoted, which folds it to lowercase.
SCHEMA_PATTERN = re.compile(r"[a-z_][a-z0-9_]{0,62}")
SELF_HOSTED_ONLY_SSLMODES = frozenset({"disable"})
SSLMODES = frozenset({"require"}) | SELF_HOSTED_ONLY_SSLMODES

_SQLSTATE_DETAILS = {
    "28P01": "Authentication failed.",
    "28000": "Authentication failed.",
    "3D000": "Database does not exist.",
    "42P01": MISSING_EVENTS_TABLE_DETAIL,
    "42501": PERMISSION_DENIED_DETAIL,
    "57014": QUERY_TIMEOUT_DETAIL,
}

# libpq reports connection-time failures without a SQLSTATE.
_CONNECT_FAILURE_SQLSTATES = (
    (re.compile(r"password authentication failed"), "28P01"),
    (re.compile(r"no pg_hba\.conf entry"), "28000"),
    (re.compile(r'database ".*" does not exist'), "3D000"),
)


def _error_sqlstate(error: psycopg2.Error) -> str | None:
    if error.pgcode:
        return error.pgcode
    message = str(error)
    for pattern, sqlstate in _CONNECT_FAILURE_SQLSTATES:
        if pattern.search(message):
            return sqlstate
    return None


def is_plain_host(host: str) -> bool:
    if HOST_PATTERN.fullmatch(host):
        return True
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def is_flagsmith_database_config(config: object) -> bool:
    return config == {"source": FLAGSMITH_DATABASE_SOURCE}


def is_flagsmith_database_postgres() -> bool:
    return connections[DEFAULT_DB_ALIAS].vendor == "postgresql"


def flagsmith_database_connect_params() -> dict[str, Any]:
    # Could be improved by using a dedicated Django database alias.
    params = connections[DEFAULT_DB_ALIAS].get_connection_params()
    params.pop("cursor_factory", None)
    return params


def describe_postgres_error(error: Exception) -> str:
    """Return a user-facing description of a failed verification, suitable for
    the connection's ``status_detail``. Raw exception text stays in the logs."""
    if isinstance(error, DeliveryConfigError):
        return str(error)
    if isinstance(error, MissingEventsTableError):
        return MISSING_EVENTS_TABLE_DETAIL
    if isinstance(error, EventsTableSchemaMismatchError):
        return SCHEMA_MISMATCH_DETAIL
    if isinstance(error, EventsTablePermissionError):
        return PERMISSION_DENIED_DETAIL
    if isinstance(error, psycopg2.Error):
        if detail := _SQLSTATE_DETAILS.get(_error_sqlstate(error) or ""):
            return detail
        if isinstance(error, psycopg2.OperationalError):
            return "Could not connect to the host."
        return "The PostgreSQL server rejected the request."
    return "Connection failed."


def _stored_connect_params_and_schema(
    connection: "WarehouseConnection",
) -> tuple[dict[str, Any], str]:
    config = typing.cast(PostgresConfig, connection.config or {})
    credentials = typing.cast(PostgresCredentials, connection.credentials or {})
    try:
        host = config["host"]
        connect_params: dict[str, Any] = {
            "host": host,
            "port": config["port"],
            "dbname": config["database"],
            "user": config["username"],
            "password": credentials["password"],
            "sslmode": config["sslmode"],
        }
        schema = config["schema"]
    except KeyError as exc:
        raise DeliveryConfigError("Stored connection details are incomplete.") from exc

    # Re-checked immediately before connecting: DNS may resolve differently
    # than it did at validation time.
    if not is_plain_host(host) or is_disallowed_host(host):
        raise DeliveryConfigError(
            "Host must not target internal or private network addresses."
        )
    return connect_params, schema


@contextmanager
def read_cursor(
    connection: "WarehouseConnection",
    *,
    statement_timeout: int,
) -> "Iterator[Cursor]":
    """Yield a cursor in a read-only transaction on the connection's schema,
    then discard the session.

    Settings are scoped to the transaction rather than passed as startup
    options, which transaction-mode poolers such as Supabase's and Neon's reject.

    Raises ``DeliveryConfigError`` if the stored configuration cannot be turned
    into a usable connection, or names the Flagsmith database on SaaS.
    """
    if is_flagsmith_database_config(connection.config):
        if is_saas():
            raise DeliveryConfigError(FLAGSMITH_DATABASE_UNAVAILABLE_DETAIL)
        connect_params = flagsmith_database_connect_params()
        schema = FLAGSMITH_DATABASE_SCHEMA
    else:
        connect_params, schema = _stored_connect_params_and_schema(connection)

    with closing(
        psycopg2.connect(
            **{
                "connect_timeout": CONNECT_TIMEOUT_SECONDS,
                "application_name": "flagsmith",
                **connect_params,
            }
        )
    ) as pg_connection:
        with pg_connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute(
                "SET LOCAL statement_timeout = %s", (f"{statement_timeout}s",)
            )
            cursor.execute("SET LOCAL TIME ZONE 'UTC'")
            cursor.execute(
                sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(schema))
            )
            yield cursor


def _fetch_bool(cursor: "Cursor") -> bool:
    row = cursor.fetchone()
    return bool(row and row[0])


def check_events_table(cursor: "Cursor", schema: str) -> None:
    """Raise if the schema or its events table is missing, unusable by the
    configured user, or its columns don't match the setup SQL.

    Privileges are checked before columns: catalogue views hide the columns of
    tables the user holds no privilege on."""
    cursor.execute(
        "SELECT has_schema_privilege(oid, 'USAGE') FROM pg_namespace "
        "WHERE nspname = %s",
        (schema,),
    )
    row = cursor.fetchone()
    if row is None:
        raise MissingEventsTableError()
    if not row[0]:
        raise EventsTablePermissionError()

    cursor.execute("SELECT to_regclass('events') IS NOT NULL")
    if not _fetch_bool(cursor):
        raise MissingEventsTableError()

    cursor.execute(
        "SELECT has_table_privilege('events', 'SELECT') "
        "AND has_table_privilege('events', 'INSERT')"
    )
    if not _fetch_bool(cursor):
        raise EventsTablePermissionError()

    cursor.execute(
        "SELECT attname, format_type(atttypid, atttypmod) FROM pg_attribute "
        "WHERE attrelid = 'events'::regclass AND attnum > 0 AND NOT attisdropped"
    )
    column_types = dict(cursor.fetchall())
    if any(
        column_types.get(column) != column_type
        for column, column_type in EVENTS_TABLE_COLUMN_TYPES.items()
    ):
        raise EventsTableSchemaMismatchError()


def _query_runner(cursor: "Cursor") -> QueryRunner:
    def run_query(query: str, params: dict[str, object]) -> QueryResult:
        cursor.execute(query, params)
        columns = [column.name for column in cursor.description or ()]
        return QueryResult(cursor.fetchall(), columns)

    return run_query


def _config_error(field: str, message: str) -> serializers.ValidationError:
    return serializers.ValidationError({"config": {field: message}})


def _validate_host(host: object) -> None:
    if not host or not isinstance(host, str):
        raise _config_error("host", "This field is required.")
    if not is_plain_host(host):
        raise _config_error("host", "Enter a single hostname or IP address.")
    if is_disallowed_host(host):
        raise _config_error(
            "host", "Host must not target internal or private network addresses."
        )


def _validate_flagsmith_database_config(config: dict[str, Any]) -> dict[str, str]:
    if not is_flagsmith_database_config(config):
        raise _config_error(
            "source", f'Must be "{FLAGSMITH_DATABASE_SOURCE}", with no other fields.'
        )
    if is_saas() or not is_flagsmith_database_postgres():
        raise serializers.ValidationError(
            {"config": FLAGSMITH_DATABASE_UNAVAILABLE_DETAIL}
        )
    return {"source": FLAGSMITH_DATABASE_SOURCE}


class PostgresWarehouse:
    def validate_config(
        self,
        config: dict[str, Any],
        *,
        stored: dict[str, Any] | None = None,
    ) -> PostgresConfig | dict[str, str]:
        if not isinstance(config, dict):
            raise serializers.ValidationError({"config": "Must be an object."})
        if "source" in config:
            return _validate_flagsmith_database_config(config)
        if is_flagsmith_database_config(stored):
            stored = None
        if unknown_keys := set(config) - set(POSTGRES_DEFAULTS):
            raise serializers.ValidationError(
                {"config": {key: "Unknown field." for key in sorted(unknown_keys)}}
            )
        base = stored if stored is not None else dict(POSTGRES_DEFAULTS)
        merged: dict[str, Any] = {**base, **config}
        _validate_host(merged["host"])
        port = merged["port"]
        if (
            isinstance(port, bool)
            or not isinstance(port, int)
            or not (1 <= port <= 65535)
        ):
            raise _config_error("port", "Enter a valid port number (1-65535).")
        for key in ("database", "username"):
            if not merged[key] or not isinstance(merged[key], str):
                raise _config_error(key, "Must be a non-empty string.")
        if not isinstance(merged["schema"], str) or not SCHEMA_PATTERN.fullmatch(
            merged["schema"]
        ):
            raise _config_error(
                "schema",
                "Use lowercase letters, numbers and underscores, not starting with a number.",
            )
        allowed_sslmodes = (
            SSLMODES - SELF_HOSTED_ONLY_SSLMODES if is_saas() else SSLMODES
        )
        if (
            not isinstance(merged["sslmode"], str)
            or merged["sslmode"] not in allowed_sslmodes
        ):
            raise _config_error(
                "sslmode", f"Must be one of: {', '.join(sorted(allowed_sslmodes))}."
            )
        return typing.cast(PostgresConfig, merged)

    def validate_credentials(self, credentials: dict[str, Any]) -> PostgresCredentials:
        if not isinstance(credentials, dict):
            raise serializers.ValidationError({"credentials": "Must be an object."})
        password = credentials.get("password")
        if not password or not isinstance(password, str):
            raise serializers.ValidationError(
                {"credentials": {"password": "This field is required."}}
            )
        return {"password": password}

    def verify(self, connection: "WarehouseConnection") -> None:
        is_flagsmith_database = is_flagsmith_database_config(connection.config)
        schema = (
            FLAGSMITH_DATABASE_SCHEMA
            if is_flagsmith_database
            else typing.cast(PostgresConfig, connection.config)["schema"]
        )
        with read_cursor(
            connection, statement_timeout=VERIFY_TIMEOUT_SECONDS
        ) as cursor:
            try:
                check_events_table(cursor, schema)
            except (MissingEventsTableError, EventsTablePermissionError) as error:
                if not is_flagsmith_database:
                    raise
                raise DeliveryConfigError(
                    FLAGSMITH_DATABASE_MISSING_EVENTS_TABLE_DETAIL
                    if isinstance(error, MissingEventsTableError)
                    else FLAGSMITH_DATABASE_PERMISSION_DENIED_DETAIL
                ) from error

    def describe_error(self, error: Exception) -> str:
        return describe_postgres_error(error)

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
            with read_cursor(
                connection, statement_timeout=EVENT_NAMES_TIMEOUT_SECONDS
            ) as cursor:
                cursor.execute(
                    event_names_query(POSTGRES_DIALECT),
                    event_names_query_params(environment_key),
                )
                rows = cursor.fetchall()
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
            with read_cursor(
                connection, statement_timeout=VERIFY_TIMEOUT_SECONDS
            ) as cursor:
                cursor.execute(
                    event_stats_query(POSTGRES_DIALECT),
                    {"environment_key": environment_key},
                )
                rows = cursor.fetchall()
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
        with read_cursor(
            connection, statement_timeout=BACKGROUND_QUERY_TIMEOUT_SECONDS
        ) as cursor:
            return read_exposure_buckets(
                _query_runner(cursor),
                POSTGRES_DIALECT,
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
        with read_cursor(
            connection, statement_timeout=BACKGROUND_QUERY_TIMEOUT_SECONDS
        ) as cursor:
            return read_results_aggregates(
                _query_runner(cursor),
                POSTGRES_DIALECT,
                environment_key=environment_key,
                feature_name=feature_name,
                window_start=window_start,
                window_end=window_end,
                specs=specs,
                granularity=granularity,
            )
