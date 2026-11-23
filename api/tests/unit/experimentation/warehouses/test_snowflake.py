import base64
import hashlib
import re
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import jwt
import pytest
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from freezegun.api import FrozenDateTimeFactory
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from requests_mock import Mocker as RequestsMockerFixture
from rest_framework import serializers

from experimentation.dataclasses import (
    MetricSpec,
    WarehouseEventNames,
    WarehouseEventStats,
)
from experimentation.models import WarehouseConnection
from experimentation.types import ExposureGranularity
from experimentation.warehouses import snowflake
from experimentation.warehouses.exceptions import (
    DeliveryConfigError,
    EventsTableSchemaMismatchError,
)
from experimentation.warehouses.snowflake import (
    EVENTS_TABLE_COLUMN_TYPES,
    SnowflakeAuthError,
    SnowflakeRequestError,
    SnowflakeTimeout,
    SnowflakeWarehouse,
)
from tests.unit.experimentation.warehouses.test_snowflake_queries import (
    CONVERSIONS_HOUR_SQL,
    EVENT_NAMES_SQL,
    EVENT_STATS_SQL,
    EXPOSURE_BUCKETS_DAY_SQL,
    EXPOSURE_BUCKETS_HOUR_SQL,
    RESULTS_NO_METRICS_SQL,
    RESULTS_SQL,
    SPECS,
)

HOST = "https://acme-org-prod.snowflakecomputing.com"
STATEMENTS_URL = f"{HOST}/api/v2/statements"
STATEMENT_HANDLE_URL = f"{STATEMENTS_URL}/01-handle"

SNOWFLAKE_EVENTS_SQL_PATH = (
    Path(__file__).resolve().parents[5] / "experimentation" / "snowflake" / "events.sql"
)
SETUP_SQL_TYPE_SYNONYMS = {"STRING": "VARCHAR"}

VALID_CONFIG = {"account_identifier": "ACME-PROD"}
DEFAULTS = {
    "warehouse": "FLAGSMITH_WH",
    "database": "FLAGSMITH",
    "schema": "FLAGSMITH_EXP",
    "role": "FLAGSMITH_ROLE",
    "user": "FLAGSMITH_SERVICE",
}

DESCRIBED_COLUMN_TYPES = {
    "ENVIRONMENT_KEY": "VARCHAR(16777216)",
    "EVENT": "VARCHAR(16777216)",
    "FEATURE_NAME": "VARCHAR(16777216)",
    "TIMESTAMP": "TIMESTAMP_NTZ(9)",
    "COLLECTED_AT": "TIMESTAMP_NTZ(9)",
    "IDENTIFIER": "VARCHAR(16777216)",
    "VALUE": "VARCHAR(16777216)",
    "TRAITS": "VARCHAR(16777216)",
    "METADATA": "VARCHAR(16777216)",
    "SDK_LANGUAGE": "VARCHAR(16777216)",
    "SDK_VERSION": "VARCHAR(16777216)",
}

WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 8, tzinfo=timezone.utc)

ENVIRONMENT_KEY_BINDING = {"type": "TEXT", "value": "env-key"}
WINDOW_BINDINGS = [
    ENVIRONMENT_KEY_BINDING,
    {"type": "TEXT", "value": "$flag_exposure"},
    {"type": "TEXT", "value": "checkout_flow"},
    {"type": "TIMESTAMP_NTZ", "value": "1767225600000000000"},
    {"type": "TIMESTAMP_NTZ", "value": "1767830400000000000"},
]
WINDOW_RANGE_BINDINGS = WINDOW_BINDINGS[3:]


def _text_bindings(*values: str) -> list[dict[str, str]]:
    return [{"type": "TEXT", "value": value} for value in values]


RESULTS_BINDINGS = [
    *WINDOW_BINDINGS,
    *_text_bindings("purchase", "page_view", "revenue", "basket_size", "signup"),
    ENVIRONMENT_KEY_BINDING,
    *_text_bindings("purchase", "page_view", "revenue", "basket_size", "signup"),
    *WINDOW_RANGE_BINDINGS,
]
CONVERSIONS_BINDINGS = [
    *WINDOW_BINDINGS,
    *_text_bindings("purchase", "signup"),
    ENVIRONMENT_KEY_BINDING,
    *_text_bindings("purchase", "signup"),
    *WINDOW_RANGE_BINDINGS,
]


pytestmark = pytest.mark.freeze_time("2026-01-01")


@pytest.fixture(autouse=True)
def sleep(freezer: FrozenDateTimeFactory, mocker: MockerFixture) -> MagicMock:
    mock: MagicMock = mocker.patch(
        "experimentation.warehouses.snowflake.time.sleep", side_effect=freezer.tick
    )
    return mock


@pytest.fixture(autouse=True)
def is_disallowed_host(mocker: MockerFixture) -> MagicMock:
    mock: MagicMock = mocker.patch.object(
        snowflake, "is_disallowed_host", return_value=False
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


def _describe_events_table_result(column_types: dict[str, str]) -> dict[str, Any]:
    columns: list[tuple[str, str, int | None]] = [
        (name, "text", None)
        for name in (
            "name",
            "type",
            "kind",
            "null?",
            "default",
            "primary key",
            "unique key",
            "check",
            "expression",
            "comment",
            "policy name",
        )
    ]
    return _succeeded(
        [*columns, ("privacy domain", "object", None)],
        [
            [name, column_type, "COLUMN", "Y", *[None] * 8]
            for name, column_type in column_types.items()
        ],
    )


def _body(
    statement: str,
    bindings: list[dict[str, str]],
    timeout: int,
    parameters: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "statement": re.sub(r"%\(\w+\)s", "?", statement),
        "timeout": timeout,
        "database": "FLAGSMITH",
        "schema": "FLAGSMITH_EXP",
        "warehouse": "FLAGSMITH_WH",
        "role": "FLAGSMITH_ROLE",
        "bindings": {
            str(position): binding for position, binding in enumerate(bindings, 1)
        },
        "parameters": parameters or {"timezone": "UTC"},
    }


def _sent(statements: Any) -> list[Any]:
    return [request.json() for request in statements.request_history]


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
        "iss": f"ACME-ORG_PROD.FLAGSMITH_SERVICE.SHA256:{fingerprint}",
        "sub": "ACME-ORG_PROD.FLAGSMITH_SERVICE",
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


def test_run__budget_spent__raises_timeout_without_submitting(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    # Given
    statements = requests_mock.post(STATEMENTS_URL, json=_succeeded())

    # When / Then
    with pytest.raises(SnowflakeTimeout):
        with snowflake.snowflake_session(
            snowflake_connection, budget_seconds=5
        ) as session:
            freezer.tick(5)
            session.run("SELECT 1", {})
    assert statements.call_count == 0


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
        ({"status_code": 503, "text": "[]"}, 503, None, None),
    ],
    ids=[
        "role-not-granted",
        "role-missing",
        "account-missing",
        "statement-failed",
        "rate-limited",
        "server-error",
        "non-object-body",
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


def test_run__statement_fails_while_polling__raises_request_error_with_codes(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, status_code=202, json=_running())
    requests_mock.get(
        STATEMENT_HANDLE_URL,
        status_code=422,
        json={"code": "100038", "sqlState": "22018", "statementHandle": "01-handle"},
    )

    # When
    with pytest.raises(SnowflakeRequestError) as exc_info:
        with snowflake.snowflake_session(
            snowflake_connection, budget_seconds=5
        ) as session:
            session.run("SELECT 1", {})

    # Then
    assert (
        exc_info.value.status_code,
        exc_info.value.error_code,
        exc_info.value.sql_state,
    ) == (422, "100038", "22018")


@pytest.mark.parametrize(
    "cancel_response",
    [
        {"json": {"code": "000604", "message": "SQL execution canceled"}},
        {"status_code": 422, "json": {"code": "000709"}},
        {"status_code": 503, "text": "unavailable"},
        {"status_code": 503, "text": "null"},
        {"exc": requests.Timeout},
    ],
    ids=[
        "cancelled",
        "already-finished",
        "server-error",
        "server-error-null-body",
        "timeout",
    ],
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
    assert poll.call_count == 4
    assert cancel.call_count == 1
    assert cancel.request_history[-1].headers[
        "X-Snowflake-Authorization-Token-Type"
    ] == ("KEYPAIR_JWT")


@pytest.mark.parametrize(
    "poll_response",
    [
        {"exc": requests.ReadTimeout},
        {"exc": requests.ConnectionError},
        {"status_code": 429, "json": _running()},
    ],
    ids=["held-open", "connection-dropped", "rate-limited"],
)
def test_run__poll_unanswered_or_rate_limited__keeps_polling_then_raises_timeout(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    poll_response: dict[str, Any],
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, status_code=202, json=_running())
    poll = requests_mock.get(STATEMENT_HANDLE_URL, **poll_response)
    cancel = requests_mock.post(f"{STATEMENT_HANDLE_URL}/cancel", json={})

    # When
    with pytest.raises(SnowflakeTimeout):
        with snowflake.snowflake_session(
            snowflake_connection, budget_seconds=5
        ) as session:
            session.run("SELECT 1", {})

    # Then
    assert poll.call_count == 4
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
        ("PRIVACY_DOMAIN", "object", None),
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
        '{"policy": "none"}',
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
            '{"policy": "none"}',
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
        "privacy_domain",
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


def test_events_table_column_types__events_sql__stay_in_sync() -> None:
    # Given
    events_sql = SNOWFLAKE_EVENTS_SQL_PATH.read_text()

    # When
    column_types = re.findall(r"^ +([A-Z_]+) +([A-Z_]+)", events_sql, re.MULTILINE)

    # Then
    assert {
        column: SETUP_SQL_TYPE_SYNONYMS.get(column_type, column_type)
        for column, column_type in column_types
    } == EVENTS_TABLE_COLUMN_TYPES


@pytest.mark.parametrize(
    "config",
    [
        {"account_identifier": "acme-prod"},
        {
            "account_identifier": (
                " https://acme-prod.snowflakecomputing.com/console/login?x=1 "
            )
        },
        {
            "account_identifier": "ACME-PROD.snowflakecomputing.com",
            "warehouse": "flagsmith_wh",
            "user": "Flagsmith_Service",
        },
    ],
    ids=["lower-case", "pasted-url", "pasted-host-and-lower-case-identifiers"],
)
def test_validate_config__valid__normalises_and_applies_defaults(
    config: dict[str, str],
) -> None:
    # Given
    warehouse = SnowflakeWarehouse()

    # When
    result = warehouse.validate_config(config)

    # Then
    assert result == {"account_identifier": "ACME-PROD", **DEFAULTS}


def test_validate_config__stored__merges_over_stored() -> None:
    # Given
    stored = {**VALID_CONFIG, **DEFAULTS, "warehouse": "BIG_WH"}

    # When
    result = SnowflakeWarehouse().validate_config({"role": "analyst"}, stored=stored)

    # Then
    assert result == {**stored, "role": "ANALYST"}


ACCOUNT_IDENTIFIER_FORM_ERROR = {
    "config": {
        "account_identifier": "Enter the account identifier in the "
        "ORGNAME-ACCOUNTNAME form."
    }
}


@pytest.mark.parametrize(
    "config, expected_errors",
    [
        ("not-a-dict", {"config": "Must be an object."}),
        (
            {**VALID_CONFIG, "private_key": "x"},
            {"config": {"private_key": "Unknown field."}},
        ),
        *(
            (
                {"account_identifier": account_identifier},
                {"config": {"account_identifier": "This field is required."}},
            )
            for account_identifier in ("", " ", 1)
        ),
        *(
            ({"account_identifier": account_identifier}, ACCOUNT_IDENTIFIER_FORM_ERROR)
            for account_identifier in (
                "xy12345.eu-west-1",
                "xy12345",
                "acme-prod.privatelink.snowflakecomputing.com",
                "-acme",
                "acme prod-x",
            )
        ),
        *(
            (
                {**VALID_CONFIG, key: value},
                {"config": {key: "Enter a valid identifier."}},
            )
            for key, value in (
                ("warehouse", ""),
                ("warehouse", 1),
                ("database", "1FLAGSMITH"),
                ("schema", "FLAGSMITH-EXP"),
                ("role", '"flagsmith_role"'),
                ("user", "FLAGSMITH.SERVICE"),
            )
        ),
    ],
)
def test_validate_config__invalid__raises_validation_error(
    config: Any,
    expected_errors: dict[str, Any],
) -> None:
    # Given
    warehouse = SnowflakeWarehouse()

    # When
    with pytest.raises(serializers.ValidationError) as exc_info:
        warehouse.validate_config(config)

    # Then
    assert exc_info.value.detail == expected_errors


def test_validate_config__disallowed_host__raises_validation_error(
    is_disallowed_host: MagicMock,
) -> None:
    # Given
    is_disallowed_host.return_value = True

    # When
    with pytest.raises(serializers.ValidationError) as exc_info:
        SnowflakeWarehouse().validate_config({"account_identifier": "acme-org_prod"})

    # Then
    assert exc_info.value.detail == {
        "config": {
            "account_identifier": (
                "Host must not target internal or private network addresses."
            )
        }
    }
    is_disallowed_host.assert_called_once_with("acme-org-prod.snowflakecomputing.com")


@pytest.mark.parametrize(
    "private_key_format",
    [serialization.PrivateFormat.PKCS8, serialization.PrivateFormat.TraditionalOpenSSL],
    ids=["pkcs8", "pkcs1"],
)
def test_validate_credentials__valid__returns_trimmed_private_key(
    snowflake_private_key: rsa.RSAPrivateKey,
    private_key_format: serialization.PrivateFormat,
) -> None:
    # Given
    pem = snowflake_private_key.private_bytes(
        serialization.Encoding.PEM, private_key_format, serialization.NoEncryption()
    ).decode()

    # When
    result = SnowflakeWarehouse().validate_credentials(
        {"private_key": f"\n  {pem}\n\n"}
    )

    # Then
    assert result == {"private_key": pem.strip()}


@pytest.mark.parametrize(
    "credentials, expected_errors",
    [
        (lambda rsa_key: "not-a-dict", {"credentials": "Must be an object."}),
        *(
            (
                credentials,
                {"credentials": {"private_key": "This field is required."}},
            )
            for credentials in (
                lambda rsa_key: {},
                lambda rsa_key: {"private_key": ""},
                lambda rsa_key: {"private_key": 1},
            )
        ),
        *(
            (
                credentials,
                {
                    "credentials": {
                        "private_key": "Enter an unencrypted private key in PEM format."
                    }
                },
            )
            for credentials in (
                lambda rsa_key: {"private_key": "not a key"},
                lambda rsa_key: {
                    "private_key": rsa_key.private_bytes(
                        serialization.Encoding.PEM,
                        serialization.PrivateFormat.PKCS8,
                        serialization.BestAvailableEncryption(b"passphrase"),
                    ).decode()
                },
                lambda rsa_key: {
                    "private_key": rsa_key.public_key()
                    .public_bytes(
                        serialization.Encoding.PEM,
                        serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                    .decode()
                },
            )
        ),
        (
            lambda rsa_key: {
                "private_key": _pem(ec.generate_private_key(ec.SECP256R1()))
            },
            {"credentials": {"private_key": "Enter an RSA private key."}},
        ),
        (
            lambda rsa_key: {
                "private_key": _pem(
                    rsa.generate_private_key(public_exponent=65537, key_size=1024)
                )
            },
            {
                "credentials": {
                    "private_key": "Enter an RSA private key of at least 2048 bits."
                }
            },
        ),
    ],
    ids=[
        "not-a-dict",
        "missing",
        "empty",
        "not-a-string",
        "not-pem",
        "encrypted",
        "public-key",
        "not-rsa",
        "rsa-1024",
    ],
)
def test_validate_credentials__invalid__raises_validation_error(
    snowflake_private_key: rsa.RSAPrivateKey,
    credentials: Callable[[rsa.RSAPrivateKey], Any],
    expected_errors: dict[str, Any],
) -> None:
    # Given
    warehouse = SnowflakeWarehouse()

    # When
    with pytest.raises(serializers.ValidationError) as exc_info:
        warehouse.validate_credentials(credentials(snowflake_private_key))

    # Then
    assert exc_info.value.detail == expected_errors


def test_verify__reachable__checks_columns_then_probes_warehouse(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    statements = requests_mock.post(
        STATEMENTS_URL,
        [
            {"json": _describe_events_table_result(DESCRIBED_COLUMN_TYPES)},
            {"json": _succeeded([("ENVIRONMENT_KEY", "text", None)], [["env-key"]])},
        ],
    )

    # When
    SnowflakeWarehouse().verify(snowflake_connection)

    # Then
    assert _sent(statements) == [
        _body("DESCRIBE TABLE events", [], 5),
        _body(
            "SELECT environment_key FROM events LIMIT 1",
            [],
            5,
            {"timezone": "UTC", "use_cached_result": "false"},
        ),
    ]


def _rejected_response(
    status_code: int, code: str, sql_state: str | None = None
) -> dict[str, Any]:
    return {
        "status_code": status_code,
        "json": {"code": code, "sqlState": sql_state, "message": "Raw Snowflake text."},
    }


DESCRIBE_EVENTS_TABLE_RESPONSE = {
    "json": _describe_events_table_result(DESCRIBED_COLUMN_TYPES)
}


@pytest.mark.parametrize(
    "responses, expected_detail",
    [
        ([_rejected_response(401, "390144")], "Authentication failed."),
        (
            [
                {
                    "status_code": 404,
                    "text": "<!DOCTYPE html><title>File not Found</title>",
                }
            ],
            "Snowflake account not found.",
        ),
        (
            [_rejected_response(400, "390186")],
            "The role does not exist or is not granted to the user.",
        ),
        (
            [_rejected_response(400, "390189")],
            "The role does not exist or is not granted to the user.",
        ),
        (
            [_rejected_response(422, "002003", "42S02")],
            "Events table not found in the configured database. Run the setup SQL to create it.",
        ),
        (
            [
                {
                    "json": _describe_events_table_result(
                        {**DESCRIBED_COLUMN_TYPES, "TIMESTAMP": "TIMESTAMP_LTZ(9)"}
                    )
                }
            ],
            "The events table's columns don't match the setup SQL.",
        ),
        (
            [
                {
                    "json": _describe_events_table_result(
                        {
                            column: column_type
                            for column, column_type in DESCRIBED_COLUMN_TYPES.items()
                            if column != "SDK_VERSION"
                        }
                    )
                }
            ],
            "The events table's columns don't match the setup SQL.",
        ),
        (
            [
                DESCRIBE_EVENTS_TABLE_RESPONSE,
                _rejected_response(422, "391920", "57P03"),
            ],
            "Warehouse not found, or the role cannot use it.",
        ),
        (
            [
                DESCRIBE_EVENTS_TABLE_RESPONSE,
                _rejected_response(422, "003001", "42501"),
            ],
            "Permission denied on the events table. The user needs SELECT and INSERT on it.",
        ),
        ([_rejected_response(408, "000630", "57014")], "The query timed out."),
        ([{"exc": requests.ConnectionError}], "Could not connect to the host."),
        (
            [{"status_code": 429, "text": "Too Many Requests"}],
            "The Snowflake account rejected the request.",
        ),
    ],
    ids=[
        "unauthenticated",
        "unknown-account",
        "role-not-granted",
        "role-missing",
        "missing-table",
        "wrong-column-type",
        "missing-column",
        "unusable-warehouse",
        "insufficient-privileges",
        "server-timeout",
        "unreachable",
        "rate-limited",
    ],
)
def test_verify__failure__raises_described_error(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    responses: list[dict[str, Any]],
    expected_detail: str,
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, responses)
    warehouse = SnowflakeWarehouse()

    # When
    with pytest.raises(Exception) as exc_info:
        warehouse.verify(snowflake_connection)

    # Then
    assert warehouse.describe_error(exc_info.value) == expected_detail


@pytest.mark.parametrize(
    "error, expected_detail",
    [
        (
            DeliveryConfigError("Stored connection details are incomplete."),
            "Stored connection details are incomplete.",
        ),
        (SnowflakeAuthError(), "Authentication failed."),
        (SnowflakeTimeout(), "The query timed out."),
        (requests.ReadTimeout(), "Could not connect to the host."),
        (
            SnowflakeRequestError(422, "000904", "42000"),
            "The events table's columns don't match the setup SQL.",
        ),
        (
            SnowflakeRequestError(404, "390404"),
            "The Snowflake account rejected the request.",
        ),
        (
            SnowflakeRequestError(None, "MULTI_PARTITION_RESULT"),
            "The Snowflake account rejected the request.",
        ),
        (
            EventsTableSchemaMismatchError(),
            "The events table's columns don't match the setup SQL.",
        ),
        (RuntimeError("raw driver detail"), "Connection failed."),
    ],
)
def test_describe_snowflake_error__error__returns_user_facing_detail(
    error: Exception,
    expected_detail: str,
) -> None:
    # Given / When
    detail = snowflake.describe_snowflake_error(error)

    # Then
    assert detail == expected_detail


def test_snowflake_session__disallowed_host__raises_config_error(
    snowflake_connection: WarehouseConnection,
    is_disallowed_host: MagicMock,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    is_disallowed_host.return_value = True

    # When / Then
    with pytest.raises(DeliveryConfigError, match="internal or private"):
        with snowflake.snowflake_session(snowflake_connection, budget_seconds=5):
            pass  # pragma: no cover
    is_disallowed_host.assert_called_once_with("acme-org-prod.snowflakecomputing.com")
    assert requests_mock.call_count == 0


@pytest.mark.parametrize(
    "method, statement_response, expected_body, expected",
    [
        (
            "get_event_names",
            _succeeded([("EVENT", "text", None)], [["purchase"], ["signup"]]),
            _body(
                EVENT_NAMES_SQL,
                [ENVIRONMENT_KEY_BINDING, {"type": "FIXED", "value": "501"}],
                15,
            ),
            WarehouseEventNames(events=["purchase", "signup"], is_truncated=False),
        ),
        (
            "get_event_stats",
            _succeeded(
                [
                    ("TOTAL", "fixed", 0),
                    ("UNIQUE_EVENTS", "fixed", 0),
                    ("LAST_EVENT_AT", "timestamp_ntz", 9),
                ],
                [["10", "2", "1791811432.625000000"]],
            ),
            _body(EVENT_STATS_SQL, [ENVIRONMENT_KEY_BINDING], 5),
            WarehouseEventStats(
                total_events_received=10,
                unique_events_count=2,
                last_event_at=datetime(
                    2026, 10, 12, 13, 23, 52, 625000, tzinfo=timezone.utc
                ),
            ),
        ),
    ],
)
def test_event_lookup__reachable__sends_expected_statement_and_caches(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    reset_cache: None,
    method: str,
    statement_response: dict[str, Any],
    expected_body: dict[str, Any],
    expected: object,
) -> None:
    # Given
    statements = requests_mock.post(STATEMENTS_URL, json=statement_response)
    lookup = getattr(SnowflakeWarehouse(), method)

    # When
    first = lookup(snowflake_connection, "env-key")
    second = lookup(snowflake_connection, "env-key")

    # Then
    assert first == second == expected
    assert _sent(statements) == [expected_body]


@pytest.mark.parametrize(
    "method, statement_response, expected_event",
    [
        (
            "get_event_names",
            {"exc": requests.ConnectionError},
            "connection.event_names_failed",
        ),
        (
            "get_event_stats",
            {"exc": requests.ConnectionError},
            "connection.event_stats_failed",
        ),
        (
            "get_event_stats",
            {
                "json": _succeeded(
                    [
                        ("TOTAL", "fixed", 0),
                        ("UNIQUE_EVENTS", "fixed", 0),
                        ("LAST_EVENT_AT", "timestamp_ntz", 9),
                    ],
                    [["1", "1", "1794824989923.000000000"]],
                )
            },
            "connection.event_stats_failed",
        ),
    ],
    ids=["event-names-unreachable", "event-stats-unreachable", "timestamp-beyond-9999"],
)
def test_event_lookup__read_fails__caches_unavailable_and_logs(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    reset_cache: None,
    log: StructuredLogCapture,
    method: str,
    statement_response: dict[str, Any],
    expected_event: str,
) -> None:
    # Given
    statements = requests_mock.post(STATEMENTS_URL, **statement_response)
    lookup = getattr(SnowflakeWarehouse(), method)

    # When
    first = lookup(snowflake_connection, "env-key")
    second = lookup(snowflake_connection, "env-key")

    # Then
    assert first is second is None
    assert statements.call_count == 1
    assert [event["event"] for event in log.events] == [expected_event]
    assert log.events[0]["environment__id"] == snowflake_connection.environment_id


@pytest.mark.parametrize(
    "granularity, expected_sql",
    [("hour", EXPOSURE_BUCKETS_HOUR_SQL), ("day", EXPOSURE_BUCKETS_DAY_SQL)],
    ids=["hour", "day"],
)
def test_get_exposure_buckets__snowflake__sends_expected_statement(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    granularity: ExposureGranularity,
    expected_sql: str,
) -> None:
    # Given
    statements = requests_mock.post(STATEMENTS_URL, json=_succeeded())

    # When
    SnowflakeWarehouse().get_exposure_buckets(
        snowflake_connection,
        environment_key="env-key",
        feature_name="checkout_flow",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        granularity=granularity,
    )

    # Then
    assert _sent(statements) == [_body(expected_sql, WINDOW_BINDINGS, 120)]


@pytest.mark.parametrize(
    "specs, expected",
    [
        (
            [],
            [
                (RESULTS_NO_METRICS_SQL, WINDOW_BINDINGS),
                (EXPOSURE_BUCKETS_HOUR_SQL, WINDOW_BINDINGS),
            ],
        ),
        (
            SPECS,
            [
                (RESULTS_SQL, RESULTS_BINDINGS),
                (CONVERSIONS_HOUR_SQL, CONVERSIONS_BINDINGS),
                (EXPOSURE_BUCKETS_HOUR_SQL, WINDOW_BINDINGS),
            ],
        ),
    ],
    ids=["no-metrics", "every-aggregation"],
)
def test_get_results_aggregates__snowflake__sends_expected_statements(
    snowflake_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    specs: list[MetricSpec],
    expected: list[tuple[str, list[dict[str, str]]]],
) -> None:
    # Given
    statements = requests_mock.post(STATEMENTS_URL, json=_succeeded())

    # When
    SnowflakeWarehouse().get_results_aggregates(
        snowflake_connection,
        environment_key="env-key",
        feature_name="checkout_flow",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        specs=specs,
        granularity="hour",
    )

    # Then
    assert _sent(statements) == [
        _body(sql, bindings, 120) for sql, bindings in expected
    ]
