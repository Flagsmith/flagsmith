import typing
from contextlib import contextmanager
from functools import lru_cache

import boto3
import clickhouse_connect
from clickhouse_connect.driver import httputil
from clickhouse_connect.driver.exceptions import (
    DatabaseError,
    OperationalError,
)
from urllib3 import PoolManager

from core.network import is_internal_address
from experimentation.ingestion_infra_service import AWS_REGION
from experimentation.types import ClickHouseConfig, ClickHouseCredentials

if typing.TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from clickhouse_connect.driver.client import Client

    from experimentation.models import WarehouseConnection

EVENTS_TABLE_NAME = "events"
EVENTS_FORMAT = "JSONEachRow"
EVENTS_COMPRESSION = "gzip"

# Objects move between these prefixes as they are delivered, so `events/` holds
# exactly the work still outstanding. `errors/` is not available: Firehose
# writes its own delivery failures there.
PENDING_PREFIX = "events/"
ARCHIVE_PREFIX = "archive/"
FAILED_PREFIX = "failed/"

CONNECT_TIMEOUT_SECONDS = 10
INSERT_TIMEOUT_SECONDS = 300


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


class DeliveryConfigError(Exception):
    """The connection's stored configuration cannot be used for delivery."""


class ObjectRejectedError(Exception):
    """The warehouse rejected this object's contents. Other objects are
    unaffected, so the object is abandoned rather than retried."""


class MissingEventsTableError(Exception):
    """The configured database has no events table to deliver into."""


# The customer's fix is the same whether verification's existence check or a
# delivery insert found the table missing.
MISSING_EVENTS_TABLE_DETAIL = (
    "Events table not found in the configured database. "
    "Run the setup SQL to create it."
)


# ClickHouse error codes raised by the object's own bytes: unparseable records,
# values that do not fit the column, constraint violations. Anything else —
# authentication (516), a missing table (60), an unreachable host — would fail
# every object equally, so it aborts the run instead of abandoning good data.
OBJECT_LEVEL_ERROR_CODES = frozenset(
    {
        6,  # CANNOT_PARSE_TEXT
        26,  # CANNOT_PARSE_QUOTED_STRING
        27,  # CANNOT_PARSE_INPUT_ASSERTION_FAILED
        38,  # CANNOT_PARSE_DATE
        41,  # CANNOT_PARSE_DATETIME
        53,  # TYPE_MISMATCH
        69,  # ARGUMENT_OUT_OF_BOUND
        72,  # CANNOT_PARSE_NUMBER
        117,  # INCORRECT_DATA
        469,  # VIOLATED_CONSTRAINT
    }
)


def describe_warehouse_error(error: Exception) -> str:
    """Return a user-facing description of a failed verification or delivery
    run, suitable for the connection's ``status_detail``. Raw exception text
    stays in the logs: it can carry internal infrastructure details."""
    if isinstance(error, DeliveryConfigError):
        return str(error)
    # OperationalError subclasses DatabaseError, so it is matched first.
    if isinstance(error, OperationalError):
        return "Could not connect to the host."
    if isinstance(error, DatabaseError):
        # 516 = AUTHENTICATION_FAILED, 81 = UNKNOWN_DATABASE, 60 = UNKNOWN_TABLE
        if error.code == 516:
            return "Authentication failed."
        if error.code == 81:
            return "Database does not exist."
        if error.code == 60:
            return MISSING_EVENTS_TABLE_DETAIL
        return "The ClickHouse server rejected the request."
    if isinstance(error, MissingEventsTableError):
        return MISSING_EVENTS_TABLE_DETAIL
    return "Connection failed."


@lru_cache(maxsize=1)
def _get_s3_client() -> "Any":
    return boto3.client("s3", region_name=AWS_REGION)


def get_pending_prefix(environment_key: str) -> str:
    return f"{PENDING_PREFIX}env_key={environment_key}/"


def list_pending_objects(bucket_name: str, environment_key: str) -> list[str]:
    """Return the keys of an environment's undelivered event objects, oldest
    first.

    Delivered objects are moved out of `events/`, so everything under the
    prefix is outstanding. The partition path is zero-padded, so the keys S3
    returns in lexicographic order are also in chronological order.
    """
    paginator = _get_s3_client().get_paginator("list_objects_v2")
    pages = paginator.paginate(
        Bucket=bucket_name,
        Prefix=get_pending_prefix(environment_key),
    )
    return [obj["Key"] for page in pages for obj in page.get("Contents", [])]


def move_object(bucket_name: str, s3_key: str, *, to_prefix: str) -> str:
    """Move a delivered or abandoned object out of `events/`, preserving its
    partition path, and return its new key.

    Copy-then-delete is not atomic: an interrupted move leaves the object in
    place, so it is delivered again on the next run. Delivery is therefore
    at-least-once, as it already is upstream of here.
    """
    destination_key = f"{to_prefix}{s3_key.removeprefix(PENDING_PREFIX)}"
    s3 = _get_s3_client()
    s3.copy_object(
        Bucket=bucket_name,
        Key=destination_key,
        CopySource={"Bucket": bucket_name, "Key": s3_key},
    )
    s3.delete_object(Bucket=bucket_name, Key=s3_key)
    return destination_key


@contextmanager
def delivery_client(
    connection: "WarehouseConnection",
    *,
    send_receive_timeout: int = INSERT_TIMEOUT_SECONDS,
) -> "Iterator[Client]":
    """Yield a ClickHouse HTTP client for a connection, reusable across every
    object delivered in one run. Verification uses the same client, so a
    connection that verifies is one that delivery can use, with a timeout
    fitting its quick queries rather than a full insert.

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

    # Re-checked immediately before connecting, as verification does: DNS may
    # resolve differently than it did at validation time, and delivery streams
    # event data to whatever it connects to.
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


def deliver_object(client: "Client", bucket_name: str, s3_key: str) -> int:
    """Stream one gzipped events object into the customer's warehouse and
    return the number of rows written.

    The body is passed through untouched — ClickHouse decompresses and parses
    it, so neither happens in this process. Delivery is at-least-once, so a
    redelivered object duplicates rows; the distinct-aware aggregates in the
    results queries account for that.
    """
    body = _get_s3_client().get_object(Bucket=bucket_name, Key=s3_key)["Body"]
    try:
        summary = client.raw_insert(
            EVENTS_TABLE_NAME,
            insert_block=body,
            fmt=EVENTS_FORMAT,
            compression=EVENTS_COMPRESSION,
        )
    except DatabaseError as exc:
        if exc.code in OBJECT_LEVEL_ERROR_CODES:
            raise ObjectRejectedError(str(exc)) from exc
        raise
    finally:
        # Releases the pooled S3 connection if the insert failed mid-read.
        body.close()
    return summary.written_rows
