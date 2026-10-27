import re
import uuid
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from typing import Any

import psycopg2
import pytest
from psycopg2 import sql
from pytest_mock import MockerFixture
from rest_framework import serializers

from experimentation.dataclasses import (
    MetricSpec,
    WarehouseEventNames,
    WarehouseEventStats,
)
from experimentation.models import MetricAggregation, WarehouseConnection
from experimentation.warehouses.constants import (
    MISSING_EVENTS_TABLE_DETAIL,
    PERMISSION_DENIED_DETAIL,
    QUERY_TIMEOUT_DETAIL,
    SCHEMA_MISMATCH_DETAIL,
)
from experimentation.warehouses.exceptions import DeliveryConfigError
from experimentation.warehouses.postgres import (
    EVENTS_TABLE_COLUMN_TYPES,
    PostgresWarehouse,
    describe_postgres_error,
    read_cursor,
)
from tests.unit.experimentation.conftest import (
    POSTGRES_EVENTS_SQL_PATH,
    PostgresWarehouseSchema,
)

ENV = "env-key"
FEATURE = "checkout_flow"
EXPOSURE = "$flag_exposure"
WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 8, tzinfo=timezone.utc)
VALID_CONFIG = {"host": "pg.example.com", "database": "analytics", "username": "fs"}
DEFAULTS = {"port": 5432, "schema": "flagsmith_exp", "sslmode": "require"}
NAIVE_TIMESTAMP = "ALTER TABLE {}.events ALTER COLUMN timestamp TYPE TIMESTAMP"
UUID_IDENTIFIER = "ALTER TABLE {}.events ALTER COLUMN identifier TYPE UUID USING NULL"
SINGLE_HOST_ERROR = {"config": {"host": "Enter a single hostname or IP address."}}

MakeRole = Callable[[list[str], bool], tuple[str, str]]
Setup = Callable[[PostgresWarehouseSchema, WarehouseConnection, MakeRole], None]


def _at(day: int, hour: int) -> datetime:
    return datetime(2026, 1, day, hour, tzinfo=timezone.utc)


def _seed(target: PostgresWarehouseSchema) -> None:
    rows = [
        (ENV, "u1", EXPOSURE, FEATURE, "control", _at(1, 10)),
        (ENV, "u2", EXPOSURE, FEATURE, "treatment", _at(1, 11)),
        (ENV, "u1", "purchase", None, None, _at(1, 12)),
        ("other-env", "u3", "signup", None, None, _at(2, 9)),
    ]
    target.cursor.executemany(
        sql.SQL(
            "INSERT INTO {}.events "
            "(environment_key, identifier, event, feature_name, value, timestamp) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        ).format(sql.Identifier(target.schema)),
        rows,
    )


def _use(connection: WarehouseConnection, **config: object) -> None:
    connection.config = {**(connection.config or {}), **config}


def _alter(target: PostgresWarehouseSchema, statement: str) -> None:
    target.cursor.execute(sql.SQL(statement).format(sql.Identifier(target.schema)))


def _login_as(connection: WarehouseConnection, role: tuple[str, str]) -> None:
    username, password = role
    _use(connection, username=username)
    connection.credentials = {"password": password}


@pytest.fixture()
def make_role(
    postgres_warehouse_schema: PostgresWarehouseSchema,
) -> Iterator[MakeRole]:
    cursor = postgres_warehouse_schema.cursor
    schema = sql.Identifier(postgres_warehouse_schema.schema)
    roles: list[sql.Identifier] = []

    def _make_role(privileges: list[str], usage: bool) -> tuple[str, str]:
        name, password = f"exp_role_{uuid.uuid4().hex[:12]}", uuid.uuid4().hex
        role = sql.Identifier(name)
        cursor.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s").format(role), (password,)
        )
        roles.append(role)
        if usage:
            cursor.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(schema, role)
            )
        for privilege in privileges:
            cursor.execute(
                sql.SQL("GRANT {} ON {}.events TO {}").format(
                    sql.SQL(privilege), schema, role
                )
            )
        return name, password

    yield _make_role
    for role in roles:
        cursor.execute(sql.SQL("DROP OWNED BY {0}; DROP ROLE {0}").format(role))


def test_events_table_columns__events_sql__match_provider() -> None:
    # Given
    ddl = POSTGRES_EVENTS_SQL_PATH.read_text()

    # When
    columns = dict(re.findall(r"^\s+(\w+)\s+(TEXT|TIMESTAMPTZ)\b", ddl, re.M))

    # Then
    assert columns == {
        name: "TEXT" if column_type == "text" else "TIMESTAMPTZ"
        for name, column_type in EVENTS_TABLE_COLUMN_TYPES.items()
    }


@pytest.mark.parametrize(
    "config, saas, expected",
    [
        (VALID_CONFIG, False, {**VALID_CONFIG, **DEFAULTS}),
        ({**VALID_CONFIG, "host": "my_db.internal"}, False, None),
        ({**VALID_CONFIG, "host": "2001:db8::1"}, False, None),
        ({**VALID_CONFIG, "sslmode": "disable"}, False, None),
        ("not-an-object", False, {"config": "Must be an object."}),
        (
            {**VALID_CONFIG, "engine": "x"},
            False,
            {"config": {"engine": "Unknown field."}},
        ),
        (
            {**VALID_CONFIG, "host": ""},
            False,
            {"config": {"host": "This field is required."}},
        ),
        ({**VALID_CONFIG, "host": "db1,127.0.0.1"}, False, SINGLE_HOST_ERROR),
        ({**VALID_CONFIG, "host": "/var/run/postgresql"}, False, SINGLE_HOST_ERROR),
        ({**VALID_CONFIG, "host": "user@db"}, False, SINGLE_HOST_ERROR),
        (
            {**VALID_CONFIG, "host": "127.0.0.1"},
            True,
            {
                "config": {
                    "host": "Host must not target internal or private network addresses."
                }
            },
        ),
        (
            {**VALID_CONFIG, "port": True},
            False,
            {"config": {"port": "Enter a valid port number (1-65535)."}},
        ),
        (
            {**VALID_CONFIG, "database": ""},
            False,
            {"config": {"database": "Must be a non-empty string."}},
        ),
        (
            {**VALID_CONFIG, "schema": "Flagsmith_Exp"},
            False,
            {
                "config": {
                    "schema": "Use lowercase letters, numbers and underscores, not starting with a number."
                }
            },
        ),
        (
            {**VALID_CONFIG, "sslmode": ["require"]},
            False,
            {"config": {"sslmode": "Must be one of: disable, require."}},
        ),
        (
            {**VALID_CONFIG, "sslmode": "disable"},
            True,
            {"config": {"sslmode": "Must be one of: require."}},
        ),
    ],
)
def test_validate_config__input__returns_config_or_field_error(
    mocker: MockerFixture,
    config: Any,
    saas: bool,
    expected: dict[str, object] | None,
) -> None:
    # Given
    mocker.patch("experimentation.warehouses.base.is_saas", return_value=saas)
    mocker.patch("experimentation.warehouses.postgres.is_saas", return_value=saas)

    # When
    try:
        result: object = PostgresWarehouse().validate_config(config)
    except serializers.ValidationError as error:
        result = error.detail

    # Then
    assert result == (expected or {**DEFAULTS, **config})


@pytest.mark.parametrize(
    "credentials, expected",
    [
        ({"password": "hunter2"}, {"password": "hunter2"}),
        ("hunter2", {"credentials": "Must be an object."}),
        ({}, {"credentials": {"password": "This field is required."}}),
    ],
)
def test_validate_credentials__input__returns_password_or_error(
    credentials: Any,
    expected: dict[str, object],
) -> None:
    # Given / When
    try:
        result: object = PostgresWarehouse().validate_credentials(credentials)
    except serializers.ValidationError as error:
        result = error.detail

    # Then
    assert result == expected


def test_read_cursor__connection__scopes_session_to_read_only_schema(
    postgres_connection: WarehouseConnection,
    postgres_warehouse_schema: PostgresWarehouseSchema,
) -> None:
    # Given / When
    with read_cursor(postgres_connection, statement_timeout=7) as cursor:
        cursor.execute(
            "SELECT current_setting('transaction_read_only'), "
            "current_setting('statement_timeout'), "
            "current_setting('TimeZone'), current_schema()"
        )
        settings = cursor.fetchone()

    # Then
    assert settings == ("on", "7s", "UTC", postgres_warehouse_schema.schema)


@pytest.mark.parametrize(
    "config",
    [{"host": "pg.example.com"}, {**VALID_CONFIG, **DEFAULTS, "host": "db1,127.0.0.1"}],
    ids=["incomplete-config", "host-list"],
)
def test_read_cursor__unusable_config__raises_before_connecting(
    mocker: MockerFixture,
    config: dict[str, object],
) -> None:
    # Given
    connect = mocker.patch("experimentation.warehouses.postgres.psycopg2.connect")
    connection = WarehouseConnection(warehouse_type="postgres", config=config)
    connection.credentials = {"password": "hunter2"}

    # When
    with pytest.raises(DeliveryConfigError):
        with read_cursor(connection, statement_timeout=5):
            pass  # pragma: no cover

    # Then
    connect.assert_not_called()


@pytest.mark.usefixtures("saas_mode")
def test_read_cursor__saas__connects_to_pinned_address(mocker: MockerFixture) -> None:
    # Given
    mocker.patch(
        "core.network.socket.getaddrinfo",
        return_value=[(None, None, None, "", ("8.8.8.8", 0))],
    )
    connect = mocker.patch(
        "experimentation.warehouses.postgres.psycopg2.connect",
        side_effect=psycopg2.OperationalError("stop"),
    )
    connection = WarehouseConnection(
        warehouse_type="postgres", config={**VALID_CONFIG, **DEFAULTS}
    )
    connection.credentials = {"password": "hunter2"}

    # When
    with pytest.raises(psycopg2.OperationalError):
        with read_cursor(connection, statement_timeout=5):
            pass  # pragma: no cover

    # Then
    assert connect.call_args.kwargs["host"] == "pg.example.com"
    assert connect.call_args.kwargs["hostaddr"] == "8.8.8.8"


@pytest.mark.parametrize(
    "setup, expected_detail",
    [
        (
            lambda target, _connection, _make_role: _alter(
                target, "DROP TABLE {}.events"
            ),
            MISSING_EVENTS_TABLE_DETAIL,
        ),
        (
            lambda _target, connection, _make_role: _use(connection, schema="missing"),
            MISSING_EVENTS_TABLE_DETAIL,
        ),
        (
            lambda target, _connection, _make_role: _alter(target, NAIVE_TIMESTAMP),
            SCHEMA_MISMATCH_DETAIL,
        ),
        (
            lambda target, _connection, _make_role: _alter(target, UUID_IDENTIFIER),
            SCHEMA_MISMATCH_DETAIL,
        ),
        (
            lambda _target, connection, make_role: _login_as(
                connection, make_role([], True)
            ),
            PERMISSION_DENIED_DETAIL,
        ),
        (
            lambda _target, connection, make_role: _login_as(
                connection, make_role(["SELECT", "INSERT"], False)
            ),
            PERMISSION_DENIED_DETAIL,
        ),
        (
            lambda _target, connection, _make_role: setattr(
                connection, "credentials", {"password": "wrong"}
            ),
            "Authentication failed.",
        ),
        (
            lambda _target, connection, _make_role: _use(
                connection, database="missing"
            ),
            "Database does not exist.",
        ),
    ],
    ids=[
        "missing-table",
        "missing-schema",
        "naive-timestamp",
        "uuid-identifier",
        "no-table-privileges",
        "no-schema-usage",
        "bad-password",
        "missing-database",
    ],
)
def test_verify__unusable_warehouse__raises_with_detail(
    postgres_connection: WarehouseConnection,
    postgres_warehouse_schema: PostgresWarehouseSchema,
    make_role: MakeRole,
    setup: Setup,
    expected_detail: str,
) -> None:
    # Given
    setup(postgres_warehouse_schema, postgres_connection, make_role)
    warehouse = PostgresWarehouse()

    # When
    with pytest.raises(Exception) as exc_info:
        warehouse.verify(postgres_connection)

    # Then
    assert warehouse.describe_error(exc_info.value) == expected_detail


def test_describe_error__server_sqlstate__maps_to_detail(
    postgres_connection: WarehouseConnection,
) -> None:
    # Given
    with pytest.raises(psycopg2.Error) as exc_info:
        with read_cursor(postgres_connection, statement_timeout=1) as cursor:
            cursor.execute("SELECT pg_sleep(2)")

    # When
    detail = describe_postgres_error(exc_info.value)

    # Then
    assert detail == QUERY_TIMEOUT_DETAIL


@pytest.mark.parametrize(
    "error, expected_detail",
    [
        (DeliveryConfigError("Incomplete."), "Incomplete."),
        (
            psycopg2.OperationalError('FATAL:  no pg_hba.conf entry for host "x"'),
            "Authentication failed.",
        ),
        (
            psycopg2.OperationalError(
                'FATAL:  database "a" is not currently accepting connections'
            ),
            "Could not connect to the host.",
        ),
        (
            psycopg2.DatabaseError("unexpected"),
            "The PostgreSQL server rejected the request.",
        ),
        (ValueError("boom"), "Connection failed."),
    ],
)
def test_describe_error__other_failures__returns_detail(
    error: Exception,
    expected_detail: str,
) -> None:
    # Given / When
    detail = describe_postgres_error(error)

    # Then
    assert detail == expected_detail


@pytest.mark.parametrize(
    "method, expected",
    [
        (
            "get_event_names",
            WarehouseEventNames(events=["purchase", EXPOSURE], is_truncated=False),
        ),
        (
            "get_event_stats",
            WarehouseEventStats(total_events_received=3, unique_events_count=2),
        ),
    ],
)
def test_event_reads__events__return_and_cache(
    postgres_connection: WarehouseConnection,
    postgres_warehouse_schema: PostgresWarehouseSchema,
    mocker: MockerFixture,
    method: str,
    expected: object,
) -> None:
    # Given
    _seed(postgres_warehouse_schema)
    connect = mocker.spy(psycopg2, "connect")
    read = getattr(PostgresWarehouse(), method)

    # When
    results = [read(postgres_connection, ENV), read(postgres_connection, ENV)]

    # Then
    assert results == [expected, expected]
    assert connect.call_count == 1


@pytest.mark.parametrize("method", ["get_event_names", "get_event_stats"])
def test_event_reads__unreachable__return_none_and_cache_failure(
    postgres_connection: WarehouseConnection,
    mocker: MockerFixture,
    method: str,
) -> None:
    # Given
    _use(postgres_connection, port=1)
    connect = mocker.spy(psycopg2, "connect")
    read = getattr(PostgresWarehouse(), method)

    # When
    results = [read(postgres_connection, ENV), read(postgres_connection, ENV)]

    # Then
    assert results == [None, None]
    assert connect.call_count == 1


def test_get_exposure_buckets__naive_column_and_non_utc_role__buckets_in_utc(
    postgres_connection: WarehouseConnection,
    postgres_warehouse_schema: PostgresWarehouseSchema,
    make_role: MakeRole,
) -> None:
    # Given
    _alter(postgres_warehouse_schema, NAIVE_TIMESTAMP)
    _seed(postgres_warehouse_schema)
    role = make_role(["SELECT"], True)
    postgres_warehouse_schema.cursor.execute(
        sql.SQL("ALTER ROLE {} SET TimeZone = 'America/New_York'").format(
            sql.Identifier(role[0])
        )
    )
    _login_as(postgres_connection, role)

    # When
    buckets = PostgresWarehouse().get_exposure_buckets(
        postgres_connection,
        environment_key=ENV,
        feature_name=FEATURE,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        granularity="day",
    )

    # Then
    # A naive column yields naive buckets; their wall-clock time must be UTC midnight.
    assert sorted(
        (bucket.variant, bucket.bucket.replace(tzinfo=timezone.utc))
        for bucket in buckets
    ) == [("control", _at(1, 0)), ("treatment", _at(1, 0))]


def test_get_results_aggregates__events__reads_customer_schema(
    postgres_connection: WarehouseConnection,
    postgres_warehouse_schema: PostgresWarehouseSchema,
) -> None:
    # Given
    _seed(postgres_warehouse_schema)
    spec = MetricSpec(1, "purchase", MetricAggregation.OCCURRENCE, False)

    # When
    aggregates = PostgresWarehouse().get_results_aggregates(
        postgres_connection,
        environment_key=ENV,
        feature_name=FEATURE,
        specs=[spec],
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        granularity="day",
    )

    # Then
    assert aggregates.exposure_counts == {"control": 1, "treatment": 1}
    assert {
        variant: stats.sum for variant, stats in aggregates.metric_stats[1].items()
    } == {
        "control": 1,
        "treatment": 0,
    }
