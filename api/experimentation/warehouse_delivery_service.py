import typing
from contextlib import contextmanager
from functools import lru_cache

import boto3
import clickhouse_connect
import structlog
from clickhouse_connect.driver.exceptions import DatabaseError

from core.network import is_internal_address
from experimentation.ingestion_infra_service import AWS_REGION
from experimentation.types import ClickHouseConfig, ClickHouseCredentials

if typing.TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from clickhouse_connect.driver.client import Client

    from experimentation.models import WarehouseConnection

logger = structlog.get_logger("experimentation")

EVENTS_TABLE_NAME = "events"
EVENTS_FORMAT = "JSONEachRow"
EVENTS_COMPRESSION = "gzip"

# Objects move between these prefixes as they are delivered, so `events/` holds
# exactly the work still outstanding. `errors/` is not available: Firehose
# writes its own delivery failures there.
PENDING_PREFIX = "events/"
ARCHIVE_PREFIX = "archive/"
FAILED_PREFIX = "failed/"

# The stored port is the native protocol port used by verification. Delivery
# needs the HTTP interface, which listens on a different port; ClickHouse
# exposes the two as a fixed pair, so it is inferred rather than asked for.
NATIVE_TO_HTTP_PORT = {9440: 8443, 9000: 8123}

CONNECT_TIMEOUT_SECONDS = 10
INSERT_TIMEOUT_SECONDS = 300


class DeliveryConfigError(Exception):
    """The connection's stored configuration cannot be used for delivery."""


class ObjectRejectedError(Exception):
    """The warehouse rejected this object's contents. Other objects are
    unaffected, so the object is abandoned rather than retried."""


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
def delivery_client(connection: "WarehouseConnection") -> "Iterator[Client]":
    """Yield a ClickHouse HTTP client for a connection, reusable across every
    object delivered in one run.

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

    if (http_port := NATIVE_TO_HTTP_PORT.get(port)) is None:
        raise DeliveryConfigError(
            f"No HTTP port is known for ClickHouse port {port}; "
            f"expected one of {sorted(NATIVE_TO_HTTP_PORT)}."
        )

    client = clickhouse_connect.get_client(
        host=host,
        port=http_port,
        username=username,
        password=password,
        database=database,
        secure=secure,
        connect_timeout=CONNECT_TIMEOUT_SECONDS,
        send_receive_timeout=INSERT_TIMEOUT_SECONDS,
    )
    try:
        yield client
    finally:
        client.close()


def deliver_object(client: "Client", bucket_name: str, s3_key: str) -> int:
    """Stream one gzipped events object into the customer's warehouse and
    return the number of rows written.

    The body is passed through untouched — ClickHouse decompresses and parses
    it, so neither happens in this process. The deduplication token is what
    absorbs a redelivery, but only on a Replicated table or one configured with
    a non-replicated deduplication window; otherwise duplicates reach the table
    and the distinct-aware aggregates in the results queries account for them.
    """
    body = _get_s3_client().get_object(Bucket=bucket_name, Key=s3_key)["Body"]
    try:
        summary = client.raw_insert(
            EVENTS_TABLE_NAME,
            insert_block=body,
            fmt=EVENTS_FORMAT,
            compression=EVENTS_COMPRESSION,
            settings={"insert_deduplication_token": s3_key},
        )
    except DatabaseError as exc:
        if exc.code in OBJECT_LEVEL_ERROR_CODES:
            raise ObjectRejectedError(str(exc)) from exc
        raise
    return summary.written_rows
