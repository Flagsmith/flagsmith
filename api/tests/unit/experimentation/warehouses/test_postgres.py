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

from environments.models import Environment
from experimentation.dataclasses import (
    ExposureBucket,
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
from experimentation.warehouses.exceptions import (
    DeliveryConfigError,
    EventsTablePermissionError,
    EventsTableSchemaMismatchError,
    MissingEventsTableError,
)
from experimentation.warehouses.postgres import (
    EVENTS_TABLE_COLUMNS,
    TIMESTAMPTZ_COLUMNS,
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

VALID_CONFIG = {
    "host": "pg.example.com",
    "database": "analytics",
    "username": "flagsmith",
}

MakeRole = Callable[[list[str], bool], tuple[str, str]]


def _at(day: int, hour: int) -> datetime:
    return datetime(2026, 1, day, hour, tzinfo=timezone.utc)


def _seed(target: PostgresWarehouseSchema) -> None:
    rows = [
        (ENV, "u1", EXPOSURE, FEATURE, "control", _at(1, 10)),
        (ENV, "u2", EXPOSURE, FEATURE, "treatment", _at(1, 11)),
        (ENV, "u1", "purchase", None, None, _at(1, 12)),
        ("other-env", "u3", "signup", None, None, _at(2, 9)),
    ]
    with target.admin.cursor() as cursor:
        cursor.executemany(
            sql.SQL(
                "INSERT INTO {}.events "
                "(environment_key, identifier, event, feature_name, value, timestamp) "
                "VALUES (%s, %s, %s, %s, %s, %s)"
            ).format(sql.Identifier(target.schema)),
            rows,
        )


@pytest.fixture()
def make_role(
    postgres_warehouse_schema: PostgresWarehouseSchema,
) -> Iterator[MakeRole]:
    roles: list[str] = []

    def _make_role(privileges: list[str], usage: bool) -> tuple[str, str]:
        role = f"exp_role_{uuid.uuid4().hex[:12]}"
        password = uuid.uuid4().hex
        schema = sql.Identifier(postgres_warehouse_schema.schema)
        postgres_warehouse_schema.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s").format(sql.Identifier(role)),
            (password,),
        )
        roles.append(role)
        if usage:
            postgres_warehouse_schema.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    schema, sql.Identifier(role)
                )
            )
        for privilege in privileges:
            postgres_warehouse_schema.execute(
                sql.SQL("GRANT {} ON {}.events TO {}").format(
                    sql.SQL(privilege), schema, sql.Identifier(role)
                )
            )
        return role, password

    yield _make_role
    for role in roles:
        postgres_warehouse_schema.execute(
            sql.SQL("DROP OWNED BY {}; DROP ROLE {}").format(
                sql.Identifier(role), sql.Identifier(role)
            )
        )


def test_events_table_columns__events_sql__match_provider() -> None:
    # Given
    ddl = POSTGRES_EVENTS_SQL_PATH.read_text()

    # When
    columns = dict(re.findall(r"^\s+(\w+)\s+(TEXT|TIMESTAMPTZ)\b", ddl, re.M))

    # Then
    assert columns.keys() == EVENTS_TABLE_COLUMNS
    assert {name for name, kind in columns.items() if kind == "TIMESTAMPTZ"} == set(
        TIMESTAMPTZ_COLUMNS
    )


def test_validate_config__minimal__applies_defaults() -> None:
    # Given / When
    config = PostgresWarehouse().validate_config(dict(VALID_CONFIG))

    # Then
    assert config == {
        **VALID_CONFIG,
        "port": 5432,
        "schema": "flagsmith_exp",
        "sslmode": "require",
    }


def test_validate_config__stored__merges_update() -> None:
    # Given
    stored = PostgresWarehouse().validate_config(dict(VALID_CONFIG))

    # When
    config = PostgresWarehouse().validate_config({"port": 6543}, stored=dict(stored))

    # Then
    assert config == {**stored, "port": 6543}


@pytest.mark.parametrize(
    "config, expected_error",
    [
        ("not-an-object", {"config": "Must be an object."}),
        ({**VALID_CONFIG, "engine": "x"}, {"config": {"engine": "Unknown field."}}),
        (
            {**VALID_CONFIG, "host": ""},
            {"config": {"host": "This field is required."}},
        ),
        (
            {**VALID_CONFIG, "port": True},
            {"config": {"port": "Enter a valid port number (1-65535)."}},
        ),
        (
            {**VALID_CONFIG, "port": 70000},
            {"config": {"port": "Enter a valid port number (1-65535)."}},
        ),
        (
            {**VALID_CONFIG, "database": ""},
            {"config": {"database": "Must be a non-empty string."}},
        ),
        (
            {**VALID_CONFIG, "username": 1},
            {"config": {"username": "Must be a non-empty string."}},
        ),
        *[
            (
                {**VALID_CONFIG, "schema": schema},
                {
                    "config": {
                        "schema": "Use lowercase letters, numbers and underscores, not starting with a number."
                    }
                },
            )
            for schema in (
                "1events",
                "flag-smith",
                "Flagsmith_Exp",
                'x"; DROP',
                "a" * 64,
                None,
            )
        ],
        *[
            (
                {**VALID_CONFIG, "host": host},
                {"config": {"host": "Enter a single hostname or IP address."}},
            )
            for host in (
                "db1,127.0.0.1",
                "/var/run/postgresql",
                "db host",
                "a=b",
                "user@db",
            )
        ],
        *[
            (
                {**VALID_CONFIG, "sslmode": sslmode},
                {"config": {"sslmode": "Must be one of: disable, require."}},
            )
            for sslmode in ("prefer", ["require"])
        ],
    ],
)
def test_validate_config__invalid__raises_field_error(
    config: Any,
    expected_error: dict[str, object],
) -> None:
    # Given / When
    with pytest.raises(serializers.ValidationError) as exc_info:
        PostgresWarehouse().validate_config(config)

    # Then
    assert exc_info.value.detail == expected_error


@pytest.mark.parametrize(
    "host",
    [
        "pg.example.com",
        "postgres",
        "flagsmith_db",
        "my_db.internal",
        "10.0.0.5",
        "2001:db8::1",
    ],
)
def test_validate_config__single_host__accepts(host: str) -> None:
    # Given / When
    config = PostgresWarehouse().validate_config({**VALID_CONFIG, "host": host})

    # Then
    assert config["host"] == host


def test_validate_config__sslmode_disable_on_saas__raises_sslmode_error(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch("experimentation.warehouses.postgres.is_saas", return_value=True)

    # When
    with pytest.raises(serializers.ValidationError) as exc_info:
        PostgresWarehouse().validate_config({**VALID_CONFIG, "sslmode": "disable"})

    # Then
    assert exc_info.value.detail == {"config": {"sslmode": "Must be one of: require."}}


def test_validate_config__sslmode_disable_on_self_hosted__accepts() -> None:
    # Given / When
    config = PostgresWarehouse().validate_config({**VALID_CONFIG, "sslmode": "disable"})

    # Then
    assert config["sslmode"] == "disable"


def test_validate_config__internal_host_on_saas__raises_host_error(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch("experimentation.warehouses.base.is_saas", return_value=True)

    # When
    with pytest.raises(serializers.ValidationError) as exc_info:
        PostgresWarehouse().validate_config({**VALID_CONFIG, "host": "127.0.0.1"})

    # Then
    assert exc_info.value.detail == {
        "config": {
            "host": "Host must not target internal or private network addresses."
        }
    }


@pytest.mark.parametrize(
    "credentials, expected",
    [
        ({"password": "hunter2"}, {"password": "hunter2"}),
        ("hunter2", {"credentials": "Must be an object."}),
        ({}, {"credentials": {"password": "This field is required."}}),
        ({"password": 1}, {"credentials": {"password": "This field is required."}}),
    ],
    ids=["valid", "not-an-object", "missing", "not-a-string"],
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
    "config, saas",
    [
        ({"host": "pg.example.com"}, False),
        (
            {
                **VALID_CONFIG,
                "host": "127.0.0.1",
                "port": 5432,
                "schema": "s",
                "sslmode": "require",
            },
            True,
        ),
        (
            {
                **VALID_CONFIG,
                "host": "db1,127.0.0.1",
                "port": 5432,
                "schema": "s",
                "sslmode": "require",
            },
            False,
        ),
    ],
    ids=["incomplete-config", "internal-host-on-saas", "host-list"],
)
def test_read_cursor__unusable_config__raises_config_error(
    environment: Environment,
    mocker: MockerFixture,
    config: dict[str, object],
    saas: bool,
) -> None:
    # Given
    mocker.patch("experimentation.warehouses.base.is_saas", return_value=saas)
    connect = mocker.patch("experimentation.warehouses.postgres.psycopg2.connect")
    connection = WarehouseConnection(
        environment=environment,
        warehouse_type="postgres",
        config=config,
    )
    connection.credentials = {"password": "hunter2"}

    # When
    with pytest.raises(DeliveryConfigError):
        with read_cursor(connection, statement_timeout=5):
            pass  # pragma: no cover

    # Then
    connect.assert_not_called()


def test_verify__ready_table__passes(
    postgres_connection: WarehouseConnection,
) -> None:
    # Given / When / Then
    PostgresWarehouse().verify(postgres_connection)


@pytest.mark.parametrize(
    "statement, expected_error, expected_detail",
    [
        ("DROP TABLE {}.events", MissingEventsTableError, MISSING_EVENTS_TABLE_DETAIL),
        (
            "ALTER TABLE {}.events DROP COLUMN sdk_version",
            EventsTableSchemaMismatchError,
            SCHEMA_MISMATCH_DETAIL,
        ),
        (
            "ALTER TABLE {}.events ALTER COLUMN timestamp TYPE TIMESTAMP",
            EventsTableSchemaMismatchError,
            SCHEMA_MISMATCH_DETAIL,
        ),
    ],
    ids=["missing-table", "missing-column", "naive-timestamp"],
)
def test_verify__unusable_table__raises_with_detail(
    postgres_connection: WarehouseConnection,
    postgres_warehouse_schema: PostgresWarehouseSchema,
    statement: str,
    expected_error: type[Exception],
    expected_detail: str,
) -> None:
    # Given
    schema = sql.Identifier(postgres_warehouse_schema.schema)
    postgres_warehouse_schema.execute(
        sql.SQL(statement).format(*[schema] * statement.count("{}"))
    )
    warehouse = PostgresWarehouse()

    # When
    with pytest.raises(expected_error) as exc_info:
        warehouse.verify(postgres_connection)

    # Then
    assert warehouse.describe_error(exc_info.value) == expected_detail


def test_verify__missing_schema__raises_missing_table(
    postgres_connection: WarehouseConnection,
) -> None:
    # Given
    postgres_connection.config = {
        **(postgres_connection.config or {}),
        "schema": "missing_schema",
    }
    warehouse = PostgresWarehouse()

    # When
    with pytest.raises(MissingEventsTableError) as exc_info:
        warehouse.verify(postgres_connection)

    # Then
    assert warehouse.describe_error(exc_info.value) == MISSING_EVENTS_TABLE_DETAIL


@pytest.mark.parametrize(
    "privileges, usage",
    [
        (["SELECT"], True),
        (["INSERT"], True),
        ([], True),
        (["SELECT", "INSERT"], False),
    ],
    ids=["select-only", "insert-only", "no-table-privileges", "no-schema-usage"],
)
def test_verify__missing_privilege__raises_permission_error(
    postgres_connection: WarehouseConnection,
    make_role: MakeRole,
    privileges: list[str],
    usage: bool,
) -> None:
    # Given
    username, password = make_role(privileges, usage)
    postgres_connection.config = {
        **(postgres_connection.config or {}),
        "username": username,
    }
    postgres_connection.credentials = {"password": password}
    warehouse = PostgresWarehouse()

    # When
    with pytest.raises(EventsTablePermissionError) as exc_info:
        warehouse.verify(postgres_connection)

    # Then
    assert warehouse.describe_error(exc_info.value) == PERMISSION_DENIED_DETAIL


@pytest.mark.parametrize(
    "overrides, expected_detail",
    [
        ({"credentials": {"password": "wrong"}}, "Authentication failed."),
        ({"config": {"database": "missing_database"}}, "Database does not exist."),
        ({"config": {"port": 1}}, "Could not connect to the host."),
    ],
    ids=["bad-password", "missing-database", "unreachable"],
)
def test_verify__connect_failure__describes_cause(
    postgres_connection: WarehouseConnection,
    overrides: dict[str, dict[str, object]],
    expected_detail: str,
) -> None:
    # Given
    postgres_connection.config = {
        **(postgres_connection.config or {}),
        **overrides.get("config", {}),
    }
    postgres_connection.credentials = overrides.get(
        "credentials", postgres_connection.credentials
    )
    warehouse = PostgresWarehouse()

    # When
    with pytest.raises(psycopg2.OperationalError) as exc_info:
        warehouse.verify(postgres_connection)

    # Then
    assert warehouse.describe_error(exc_info.value) == expected_detail


def test_describe_error__server_reported_sqlstate__maps_to_detail(
    postgres_connection: WarehouseConnection,
) -> None:
    # Given
    with pytest.raises(psycopg2.Error) as exc_info:
        with read_cursor(postgres_connection, statement_timeout=1) as cursor:
            cursor.execute("SELECT pg_sleep(2)")

    # When
    detail = describe_postgres_error(exc_info.value)

    # Then
    assert exc_info.value.pgcode == "57014"
    assert detail == QUERY_TIMEOUT_DETAIL


@pytest.mark.parametrize(
    "error, expected_detail",
    [
        (
            DeliveryConfigError("Stored connection details are incomplete."),
            "Stored connection details are incomplete.",
        ),
        (
            psycopg2.OperationalError(
                'FATAL:  no pg_hba.conf entry for host "1.2.3.4"'
            ),
            "Authentication failed.",
        ),
        (
            psycopg2.DatabaseError("unexpected"),
            "The PostgreSQL server rejected the request.",
        ),
        (
            psycopg2.OperationalError(
                'FATAL:  database "analytics" is not currently accepting connections'
            ),
            "Could not connect to the host.",
        ),
        (ValueError("boom"), "Connection failed."),
    ],
    ids=["config", "pg-hba", "other-database-error", "database-unavailable", "other"],
)
def test_describe_error__other_failures__returns_detail(
    error: Exception,
    expected_detail: str,
) -> None:
    # Given / When / Then
    assert describe_postgres_error(error) == expected_detail


def test_get_event_names__events__returns_latest_first_and_caches(
    postgres_connection: WarehouseConnection,
    postgres_warehouse_schema: PostgresWarehouseSchema,
    mocker: MockerFixture,
) -> None:
    # Given
    _seed(postgres_warehouse_schema)
    connect = mocker.spy(psycopg2, "connect")
    warehouse = PostgresWarehouse()

    # When
    first = warehouse.get_event_names(postgres_connection, ENV)
    second = warehouse.get_event_names(postgres_connection, ENV)

    # Then
    assert (
        first
        == second
        == WarehouseEventNames(events=["purchase", EXPOSURE], is_truncated=False)
    )
    assert connect.call_count == 1


def test_get_event_stats__events__counts_environment_and_caches(
    postgres_connection: WarehouseConnection,
    postgres_warehouse_schema: PostgresWarehouseSchema,
    mocker: MockerFixture,
) -> None:
    # Given
    _seed(postgres_warehouse_schema)
    connect = mocker.spy(psycopg2, "connect")
    warehouse = PostgresWarehouse()

    # When
    first = warehouse.get_event_stats(postgres_connection, ENV)
    second = warehouse.get_event_stats(postgres_connection, ENV)

    # Then
    assert (
        first
        == second
        == WarehouseEventStats(total_events_received=3, unique_events_count=2)
    )
    assert connect.call_count == 1


@pytest.mark.parametrize("method", ["get_event_names", "get_event_stats"])
def test_event_reads__unreachable__return_none_and_cache_failure(
    postgres_connection: WarehouseConnection,
    mocker: MockerFixture,
    method: str,
) -> None:
    # Given
    postgres_connection.config = {**(postgres_connection.config or {}), "port": 1}
    connect = mocker.spy(psycopg2, "connect")
    read = getattr(PostgresWarehouse(), method)

    # When
    first = read(postgres_connection, ENV)
    second = read(postgres_connection, ENV)

    # Then
    assert first is second is None
    assert connect.call_count == 1


def test_get_exposure_buckets__naive_column_and_non_utc_role__buckets_in_utc(
    postgres_connection: WarehouseConnection,
    postgres_warehouse_schema: PostgresWarehouseSchema,
    make_role: MakeRole,
) -> None:
    # Given
    postgres_warehouse_schema.execute(
        sql.SQL("ALTER TABLE {}.events ALTER COLUMN timestamp TYPE TIMESTAMP").format(
            sql.Identifier(postgres_warehouse_schema.schema)
        )
    )
    _seed(postgres_warehouse_schema)
    username, password = make_role(["SELECT"], True)
    postgres_warehouse_schema.execute(
        sql.SQL("ALTER ROLE {} SET TimeZone = 'America/New_York'").format(
            sql.Identifier(username)
        )
    )
    postgres_connection.config = {
        **(postgres_connection.config or {}),
        "username": username,
    }
    postgres_connection.credentials = {"password": password}

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


def test_get_exposure_buckets__events__reads_customer_schema(
    postgres_connection: WarehouseConnection,
    postgres_warehouse_schema: PostgresWarehouseSchema,
) -> None:
    # Given
    _seed(postgres_warehouse_schema)

    # When
    buckets = PostgresWarehouse().get_exposure_buckets(
        postgres_connection,
        environment_key=ENV,
        feature_name=FEATURE,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        granularity="hour",
    )

    # Then
    assert sorted(buckets, key=lambda bucket: bucket.variant) == [
        ExposureBucket("control", _at(1, 10), 1, False),
        ExposureBucket("treatment", _at(1, 11), 1, False),
    ]


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
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        specs=[spec],
        granularity="day",
    )

    # Then
    assert aggregates.exposure_counts == {"control": 1, "treatment": 1}
    assert {
        variant: stats.sum for variant, stats in aggregates.metric_stats[1].items()
    } == {"control": 1, "treatment": 0}
