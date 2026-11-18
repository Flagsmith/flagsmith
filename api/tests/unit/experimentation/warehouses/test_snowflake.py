import base64
import hashlib
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import jwt
import pytest
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from freezegun.api import FrozenDateTimeFactory
from pytest_mock import MockerFixture
from requests_mock import Mocker as RequestsMockerFixture

from experimentation.models import WarehouseConnection, WarehouseType
from experimentation.warehouses import snowflake
from experimentation.warehouses.exceptions import (
    DeliveryConfigError,
    UnsupportedWarehouseOperation,
)
from experimentation.warehouses.snowflake import (
    SnowflakeAuthError,
    SnowflakeRequestError,
    SnowflakeTimeout,
    SnowflakeWarehouse,
)

HOST = "https://acme-org-prod.snowflakecomputing.com"
STATEMENTS_URL = f"{HOST}/api/v2/statements"
STATEMENT_HANDLE_URL = f"{STATEMENTS_URL}/01-handle"

WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 8, tzinfo=timezone.utc)


pytestmark = pytest.mark.freeze_time("2026-01-01")


@pytest.fixture(autouse=True)
def sleep(freezer: FrozenDateTimeFactory, mocker: MockerFixture) -> MagicMock:
    mock: MagicMock = mocker.patch(
        "experimentation.warehouses.snowflake.time.sleep", side_effect=freezer.tick
    )
    return mock


def _succeeded(
    columns: list[tuple[str, str, int | None]] | None = None,
    rows: list[list[str | None]] | None = None,
    partitions: int = 1,
) -> dict[str, Any]:
    return {
        "statementHandle": "01-handle",
        "resultSetMetaData": {
            "rowType": [
                {"name": name, "type": type_name, "scale": scale, "nullable": True}
                for name, type_name, scale in columns or []
            ],
            "partitionInfo": [{"rowCount": len(rows or [])}] * partitions,
        },
        "data": rows or [],
    }


def _running() -> dict[str, Any]:
    return {
        "code": "333334",
        "message": "Asynchronous execution in progress.",
        "statementHandle": "01-handle",
        "statementStatusUrl": "/api/v2/statements/01-handle",
    }


def _pem(private_key: rsa.RSAPrivateKey | ec.EllipticCurvePrivateKey) -> str:
    return private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


@pytest.mark.parametrize(
    "operation",
    [
        lambda warehouse, connection: warehouse.validate_credentials({"token": "x"}),
        lambda warehouse, connection: warehouse.verify(connection),
        lambda warehouse, connection: warehouse.describe_error(Exception()),
        lambda warehouse, connection: warehouse.get_event_names(connection, "key"),
        lambda warehouse, connection: warehouse.get_event_stats(connection, "key"),
        lambda warehouse, connection: warehouse.get_exposure_buckets(
            connection,
            environment_key="key",
            feature_name="checkout",
            window_start=WINDOW_START,
            window_end=WINDOW_END,
            granularity="day",
        ),
        lambda warehouse, connection: warehouse.get_results_aggregates(
            connection,
            environment_key="key",
            feature_name="checkout",
            window_start=WINDOW_START,
            window_end=WINDOW_END,
            specs=[],
            granularity="day",
        ),
    ],
    ids=[
        "validate_credentials",
        "verify",
        "describe_error",
        "event_names",
        "event_stats",
        "exposure_buckets",
        "results_aggregates",
    ],
)
def test_snowflake_warehouse__operation_beyond_configuration__raises_unsupported(
    operation: Callable[[SnowflakeWarehouse, WarehouseConnection], object],
) -> None:
    # Given
    connection = WarehouseConnection(
        warehouse_type=WarehouseType.SNOWFLAKE,
        config={"account_identifier": "acme"},
    )

    # When / Then
    with pytest.raises(UnsupportedWarehouseOperation):
        operation(SnowflakeWarehouse(), connection)


@pytest.mark.parametrize(
    "config, credentials",
    [
        ({"account_identifier": "acme"}, {"private_key": "pem"}),
        (
            {
                "account_identifier": "acme",
                "warehouse": "FLAGSMITH_WH",
                "database": "FLAGSMITH",
                "schema": "FLAGSMITH_EXP",
                "role": "FLAGSMITH_ROLE",
                "user": "FLAGSMITH_SERVICE",
            },
            None,
        ),
    ],
    ids=["incomplete-config", "missing-credentials"],
)
def test_snowflake_session__incomplete_details__raises_config_error(
    snowflake_connection: WarehouseConnection,
    config: dict[str, object],
    credentials: dict[str, object] | None,
) -> None:
    # Given
    snowflake_connection.config = config
    snowflake_connection.credentials = credentials

    # When / Then
    with pytest.raises(DeliveryConfigError, match="incomplete"):
        with snowflake.snowflake_session(snowflake_connection, budget_seconds=5):
            pass  # pragma: no cover


def test_snowflake_session__account_identifier_escaping_host__raises_config_error(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    snowflake_connection.config = {
        **(snowflake_connection.config or {}),
        "account_identifier": "169.254.169.254/latest#",
    }

    # When / Then
    with pytest.raises(DeliveryConfigError, match="Account identifier"):
        with snowflake.snowflake_session(snowflake_connection, budget_seconds=5):
            pass  # pragma: no cover
    assert requests_mock.call_count == 0


@pytest.mark.parametrize(
    "private_key",
    [
        lambda rsa_key: "not a key",
        lambda rsa_key: rsa_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(b"passphrase"),
        ).decode(),
        lambda rsa_key: _pem(ec.generate_private_key(ec.SECP256R1())),
    ],
    ids=["not-pem", "encrypted", "not-rsa"],
)
def test_snowflake_session__unusable_private_key__raises_auth_error(
    snowflake_connection: WarehouseConnection,
    snowflake_private_key: rsa.RSAPrivateKey,
    private_key: Callable[[rsa.RSAPrivateKey], str],
) -> None:
    # Given
    snowflake_connection.credentials = {
        "private_key": private_key(snowflake_private_key)
    }

    # When / Then
    with pytest.raises(SnowflakeAuthError):
        with snowflake.snowflake_session(snowflake_connection, budget_seconds=5):
            pass  # pragma: no cover


def test_run__statement__sends_key_pair_authenticated_request(
    snowflake_connection: WarehouseConnection,
    snowflake_private_key: rsa.RSAPrivateKey,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    statements = requests_mock.post(STATEMENTS_URL, json=_succeeded())

    # When
    with snowflake.snowflake_session(
        snowflake_connection, budget_seconds=15
    ) as session:
        session.run("SELECT 1", {})

    # Then
    request = statements.request_history[-1]
    assert request.json() == {
        "statement": "SELECT 1",
        "timeout": 15,
        "database": "FLAGSMITH",
        "schema": "FLAGSMITH_EXP",
        "warehouse": "FLAGSMITH_WH",
        "role": "FLAGSMITH_ROLE",
        "bindings": {},
        "parameters": {"timezone": "UTC"},
    }
    assert uuid.UUID(request.qs["requestid"][0]).version == 4
    assert request.headers["X-Snowflake-Authorization-Token-Type"] == "KEYPAIR_JWT"
    assert request.headers["Accept"] == "application/json"
    assert request.headers["User-Agent"] == "Flagsmith"
    public_key = snowflake_private_key.public_key()
    fingerprint = base64.b64encode(
        hashlib.sha256(
            public_key.public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        ).digest()
    ).decode()
    token = request.headers["Authorization"].removeprefix("Bearer ")
    assert jwt.decode(token, public_key, algorithms=["RS256"]) == {
        "iss": f"ACME_ORG-PROD.FLAGSMITH_SERVICE.SHA256:{fingerprint}",
        "sub": "ACME_ORG-PROD.FLAGSMITH_SERVICE",
        "iat": 1767225600,
        "exp": 1767225600 + 59 * 60,
    }


@pytest.mark.parametrize(
    "budget_seconds, expected_timeout",
    [(0.4, 1), (4.2, 5), (120, 120)],
    ids=["below-minimum", "fractional", "within-budget"],
)
def test_run__budget__bounds_statement_timeout(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    budget_seconds: float,
    expected_timeout: int,
) -> None:
    # Given
    statements = requests_mock.post(STATEMENTS_URL, json=_succeeded())

    # When
    with snowflake.snowflake_session(
        snowflake_connection, budget_seconds=budget_seconds
    ) as session:
        session.run("SELECT 1", {})

    # Then
    request = statements.request_history[-1]
    connect_and_read_timeouts: object = request.timeout
    assert request.json()["timeout"] == expected_timeout
    assert connect_and_read_timeouts == (5, expected_timeout + 5)


def test_run__params__rewrites_placeholders_to_positional_bindings(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    statements = requests_mock.post(STATEMENTS_URL, json=_succeeded())
    window_start = datetime(
        2026, 1, 1, 2, 0, 0, 123456, tzinfo=timezone(timedelta(hours=2))
    )

    # When
    with snowflake.snowflake_session(snowflake_connection, budget_seconds=5) as session:
        session.run(
            "SELECT event FROM events WHERE environment_key = %(environment_key)s "
            "AND timestamp >= %(window_start)s AND event IN (%(event)s, %(event)s) "
            "AND value > %(ratio)s LIMIT %(limit)s",
            {
                "environment_key": "env-key",
                "window_start": window_start,
                "event": "purchase",
                "ratio": 1.5,
                "limit": 501,
                "unused": "x",
            },
        )

    # Then
    body = statements.request_history[-1].json()
    assert body["statement"] == (
        "SELECT event FROM events WHERE environment_key = ? "
        "AND timestamp >= ? AND event IN (?, ?) AND value > ? LIMIT ?"
    )
    assert body["bindings"] == {
        "1": {"type": "TEXT", "value": "env-key"},
        "2": {"type": "TIMESTAMP_NTZ", "value": "1767225600123456000"},
        "3": {"type": "TEXT", "value": "purchase"},
        "4": {"type": "TEXT", "value": "purchase"},
        "5": {"type": "REAL", "value": "1.5"},
        "6": {"type": "FIXED", "value": "501"},
    }


@pytest.mark.parametrize(
    "value, expected_error",
    [
        (datetime(2026, 1, 1), ValueError),
        (True, TypeError),
        (None, TypeError),
    ],
    ids=["naive-datetime", "bool", "none"],
)
def test_run__unsupported_param__raises(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    value: object,
    expected_error: type[Exception],
) -> None:
    # Given
    statements = requests_mock.post(STATEMENTS_URL, json=_succeeded())

    # When / Then
    with pytest.raises(expected_error):
        with snowflake.snowflake_session(
            snowflake_connection, budget_seconds=5
        ) as session:
            session.run("SELECT %(value)s", {"value": value})
    assert statements.call_count == 0


@pytest.mark.parametrize(
    "response, expected_status_code, expected_error_code, expected_sql_state",
    [
        (
            {
                "status_code": 400,
                "json": {
                    "code": "390186",
                    "message": "Role 'ACCOUNTADMIN' specified in the connect string is not granted to this user.",
                },
            },
            400,
            "390186",
            None,
        ),
        (
            {
                "status_code": 400,
                "json": {
                    "code": "390189",
                    "message": "Role 'NOPE_ROLE' specified in the connect string does not exist or not authorized.",
                },
            },
            400,
            "390189",
            None,
        ),
        (
            {
                "status_code": 404,
                "text": "<!DOCTYPE html><title>File not Found</title>",
            },
            404,
            None,
            None,
        ),
        (
            {
                "status_code": 422,
                "json": {
                    "code": "002003",
                    "sqlState": "42S02",
                    "message": "SQL compilation error:\nObject 'EVENTS' does not exist or not authorized.",
                    "statementHandle": "01-handle",
                },
            },
            422,
            "002003",
            "42S02",
        ),
        ({"status_code": 429, "text": "Too Many Requests"}, 429, None, None),
        ({"status_code": 503, "text": "Service Unavailable"}, 503, None, None),
    ],
    ids=[
        "role-not-granted",
        "role-missing",
        "account-missing",
        "statement-failed",
        "rate-limited",
        "server-error",
    ],
)
def test_run__rejected__raises_request_error_with_codes(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    response: dict[str, Any],
    expected_status_code: int,
    expected_error_code: str | None,
    expected_sql_state: str | None,
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, **response)

    # When
    with pytest.raises(SnowflakeRequestError) as exc_info:
        with snowflake.snowflake_session(
            snowflake_connection, budget_seconds=5
        ) as session:
            session.run("SELECT 1 FROM events", {})

    # Then
    assert exc_info.value.status_code == expected_status_code
    assert exc_info.value.error_code == expected_error_code
    assert exc_info.value.sql_state == expected_sql_state


@pytest.mark.parametrize(
    "response, expected_error",
    [
        (
            {
                "status_code": 401,
                "json": {"code": "390144", "message": "JWT token is invalid."},
            },
            SnowflakeAuthError,
        ),
        (
            {
                "status_code": 408,
                "json": {
                    "code": "000630",
                    "sqlState": "57014",
                    "message": "Statement reached its statement or warehouse timeout of 2 second(s) and was canceled.",
                },
            },
            SnowflakeTimeout,
        ),
    ],
    ids=["unauthenticated", "server-timeout"],
)
def test_run__rejected__raises_typed_error_caused_by_request_error(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    response: dict[str, Any],
    expected_error: type[Exception],
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, **response)

    # When
    with pytest.raises(expected_error) as exc_info:
        with snowflake.snowflake_session(
            snowflake_connection, budget_seconds=5
        ) as session:
            session.run("SELECT 1", {})

    # Then
    cause = exc_info.value.__cause__
    assert isinstance(cause, SnowflakeRequestError)
    assert (cause.status_code, cause.error_code, cause.sql_state) == (
        response["status_code"],
        response["json"]["code"],
        response["json"].get("sqlState"),
    )


def test_run__redirect__is_not_followed(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    requests_mock.post(
        STATEMENTS_URL,
        status_code=302,
        headers={"Location": "http://169.254.169.254/latest"},
    )
    metadata = requests_mock.post("http://169.254.169.254/latest", json={})

    # When
    with pytest.raises(SnowflakeRequestError) as exc_info:
        with snowflake.snowflake_session(
            snowflake_connection, budget_seconds=5
        ) as session:
            session.run("SELECT 1", {})

    # Then
    assert exc_info.value.status_code == 302
    assert exc_info.value.error_code is None
    assert metadata.call_count == 0


def test_run__still_running__polls_until_done(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    sleep: MagicMock,
) -> None:
    # Given
    statements = requests_mock.post(STATEMENTS_URL, status_code=202, json=_running())
    poll = requests_mock.get(
        STATEMENT_HANDLE_URL,
        [
            {"status_code": 202, "json": _running()},
            {"json": _succeeded([("N", "fixed", 0)], [["42"]])},
        ],
    )

    # When
    with snowflake.snowflake_session(
        snowflake_connection, budget_seconds=120
    ) as session:
        result = session.run("SELECT count(*) AS n FROM events", {})

    # Then
    assert result == ([[42]], ["n"])
    assert poll.call_count == 2
    assert (
        poll.request_history[-1].headers["Authorization"]
        == statements.request_history[-1].headers["Authorization"]
    )
    assert sleep.call_count == 2


@pytest.mark.parametrize(
    "cancel_response",
    [
        {"json": {"code": "000604", "message": "SQL execution canceled"}},
        {"status_code": 422, "json": {"code": "000709"}},
        {"status_code": 503, "text": "unavailable"},
        {"exc": requests.Timeout},
    ],
    ids=["cancelled", "already-finished", "server-error", "timeout"],
)
def test_run__deadline_reached__cancels_and_raises_timeout(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    cancel_response: dict[str, Any],
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, status_code=202, json=_running())
    poll = requests_mock.get(STATEMENT_HANDLE_URL, status_code=202, json=_running())
    cancel = requests_mock.post(f"{STATEMENT_HANDLE_URL}/cancel", **cancel_response)

    # When
    with pytest.raises(SnowflakeTimeout):
        with snowflake.snowflake_session(
            snowflake_connection, budget_seconds=5
        ) as session:
            session.run("SELECT 1", {})

    # Then
    assert poll.call_count == 5
    assert cancel.call_count == 1
    assert cancel.request_history[-1].headers[
        "X-Snowflake-Authorization-Token-Type"
    ] == ("KEYPAIR_JWT")


@pytest.mark.parametrize(
    "poll_error",
    [requests.ReadTimeout, requests.ConnectionError],
    ids=["held-open", "connection-dropped"],
)
def test_run__poll_fails__retries_then_raises_timeout(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    poll_error: type[Exception],
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, status_code=202, json=_running())
    poll = requests_mock.get(STATEMENT_HANDLE_URL, exc=poll_error)
    cancel = requests_mock.post(f"{STATEMENT_HANDLE_URL}/cancel", json={})

    # When
    with pytest.raises(SnowflakeTimeout):
        with snowflake.snowflake_session(
            snowflake_connection, budget_seconds=5
        ) as session:
            session.run("SELECT 1", {})

    # Then
    assert poll.call_count == 5
    assert cancel.call_count == 1


def test_run__typed_columns__converts_values(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    columns: list[tuple[str, str, int | None]] = [
        ("TOTAL", "fixed", 0),
        ("RATE", "fixed", 2),
        ("RATIO", "real", None),
        ("EVENT", "text", None),
        ("YES", "boolean", None),
        ("NO", "boolean", None),
        ("AT_NTZ", "timestamp_ntz", 9),
        ("AT_LTZ", "timestamp_ltz", 9),
        ("MISSING", "text", None),
    ]
    row: list[str | None] = [
        "42",
        "3.25",
        "1.5",
        "control",
        "true",
        "false",
        "1767225600.123456789",
        "1767225600.000000000",
        None,
    ]
    requests_mock.post(STATEMENTS_URL, json=_succeeded(columns, [row]))

    # When
    with snowflake.snowflake_session(snowflake_connection, budget_seconds=5) as session:
        rows, names = session.run("SELECT 1", {})

    # Then
    midnight = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert rows == [
        [
            42,
            3.25,
            1.5,
            "control",
            True,
            False,
            midnight + timedelta(microseconds=123456),
            midnight,
            None,
        ]
    ]
    assert [type(value) for value in rows[0][:3]] == [int, float, float]
    last_event_at = rows[0][6]
    assert isinstance(last_event_at, datetime)
    assert last_event_at.isoformat() == "2026-01-01T00:00:00.123456+00:00"
    assert names == [
        "total",
        "rate",
        "ratio",
        "event",
        "yes",
        "no",
        "at_ntz",
        "at_ltz",
        "missing",
    ]


@pytest.mark.parametrize(
    "payload, expected_error, expected_message",
    [
        (
            _succeeded([("EVENT", "text", None)], [["purchase"]], partitions=2),
            SnowflakeRequestError,
            "MULTI_PARTITION_RESULT",
        ),
        (
            _succeeded([("AT", "timestamp_tz", 9)], [["1767225600.0 1440"]]),
            KeyError,
            "timestamp_tz",
        ),
    ],
    ids=["multi-partition", "unsupported-type"],
)
def test_run__unusable_result__raises(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    payload: dict[str, Any],
    expected_error: type[Exception],
    expected_message: str,
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, json=payload)

    # When / Then
    with pytest.raises(expected_error, match=expected_message):
        with snowflake.snowflake_session(
            snowflake_connection, budget_seconds=5
        ) as session:
            session.run("SELECT 1", {})
