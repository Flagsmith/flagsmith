import typing
from contextlib import contextmanager
from functools import lru_cache

import clickhouse_connect
from clickhouse_connect.driver import httputil
from clickhouse_connect.driver.exceptions import (
    DatabaseError,
    OperationalError,
)
from urllib3 import PoolManager

from core.network import is_internal_address
from experimentation.types import ClickHouseConfig, ClickHouseCredentials

if typing.TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from clickhouse_connect.driver.client import Client

    from experimentation.models import WarehouseConnection

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


class DeliveryConfigError(Exception):
    """The connection's stored configuration cannot be used to reach the
    warehouse."""


class MissingEventsTableError(Exception):
    """The configured database has no events table to deliver into."""


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
