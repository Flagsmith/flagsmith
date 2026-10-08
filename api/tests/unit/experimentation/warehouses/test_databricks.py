from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests
from pytest_mock import MockerFixture
from requests_mock import Mocker as RequestsMockerFixture

from experimentation.models import WarehouseConnection
from experimentation.warehouses import databricks
from experimentation.warehouses.databricks import (
    DatabricksAuthError,
    DatabricksRequestError,
    DatabricksSecretScopeError,
    DatabricksTimeout,
    DatabricksWarehouseStarting,
)
from experimentation.warehouses.exceptions import DeliveryConfigError

HOST = "https://acme.cloud.databricks.com"
TOKEN_URL = f"{HOST}/oidc/v1/token"
STATEMENTS_URL = f"{HOST}/api/2.0/sql/statements"

VALID_CONFIG = {
    "host": "acme.cloud.databricks.com",
    "workspace_id": "1234567890",
    "region": "us-east-1",
    "warehouse_id": "abc123",
    "catalog": "main",
}


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture(autouse=True)
def clock(mocker: MockerFixture) -> FakeClock:
    fake = FakeClock()
    mocker.patch.object(databricks, "time", fake)
    return fake


@pytest.fixture(autouse=True)
def is_internal_address(mocker: MockerFixture) -> MagicMock:
    mock: MagicMock = mocker.patch.object(
        databricks, "is_internal_address", return_value=False
    )
    return mock


@pytest.fixture()
def token(requests_mock: RequestsMockerFixture) -> Any:
    return requests_mock.post(
        TOKEN_URL,
        json={"access_token": "t0k3n"},
    )


def _succeeded(
    columns: list[tuple[str, str]] | None = None,
    rows: list[list[str | None]] | None = None,
) -> dict[str, Any]:
    return {
        "statement_id": "st-1",
        "status": {"state": "SUCCEEDED"},
        "manifest": {
            "schema": {
                "columns": [
                    {"name": name, "type_name": type_name}
                    for name, type_name in columns or []
                ]
            }
        },
        "result": {"data_array": rows or []},
    }


def _state(state: str) -> dict[str, Any]:
    return {"statement_id": "st-1", "status": {"state": state}}


@pytest.mark.parametrize(
    "config, credentials",
    [
        (
            {"host": "acme.cloud.databricks.com"},
            {"client_id": "a", "client_secret": "b"},
        ),
        (VALID_CONFIG | {"schema": "s"}, None),
    ],
    ids=["incomplete-config", "missing-credentials"],
)
def test_databricks_session__incomplete_details__raises_config_error(
    databricks_connection: WarehouseConnection,
    config: dict[str, object],
    credentials: dict[str, object] | None,
) -> None:
    # Given
    databricks_connection.config = config
    databricks_connection.credentials = credentials

    # When / Then
    with pytest.raises(DeliveryConfigError, match="incomplete"):
        with databricks.databricks_session(databricks_connection, budget_seconds=5):
            pass  # pragma: no cover


def test_databricks_session__internal_host__raises_config_error(
    databricks_connection: WarehouseConnection,
    is_internal_address: MagicMock,
) -> None:
    # Given
    is_internal_address.return_value = True

    # When / Then
    with pytest.raises(DeliveryConfigError, match="internal or private"):
        with databricks.databricks_session(databricks_connection, budget_seconds=5):
            pass  # pragma: no cover


@pytest.mark.parametrize(
    "budget_seconds, token_seconds, expected_wait",
    [(3, 0, "0s"), (5, 0.4, "5s"), (15, 0, "15s"), (120, 0, "30s")],
    ids=["below-minimum", "token-used-part-of-budget", "within-budget", "capped"],
)
def test_run__budget__bounds_wait_timeout(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    clock: FakeClock,
    budget_seconds: int,
    token_seconds: float,
    expected_wait: str,
) -> None:
    # Given
    def slow_token(request: Any, context: Any) -> dict[str, str]:
        clock.sleep(token_seconds)
        return {"access_token": "t0k3n"}

    requests_mock.post(TOKEN_URL, json=slow_token)
    statement = requests_mock.post(STATEMENTS_URL, json=_succeeded())

    # When
    with databricks.databricks_session(
        databricks_connection, budget_seconds=budget_seconds
    ) as session:
        session.run("SELECT 1", {})

    # Then
    assert statement.request_history[-1].json()["wait_timeout"] == expected_wait


def test_run__pending_then_succeeded__polls_until_done(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token: Any,
    clock: FakeClock,
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, json=_state("PENDING"))
    poll = requests_mock.get(
        f"{STATEMENTS_URL}/st-1",
        [
            {"json": _state("RUNNING")},
            {"json": _succeeded([("n", "BIGINT")], [["42"]])},
        ],
    )

    # When
    with databricks.databricks_session(
        databricks_connection, budget_seconds=120
    ) as session:
        result = session.run("SELECT count(*) AS n FROM events", {})

    # Then
    assert result == ([[42]], ["n"])
    assert poll.call_count == 2
    assert poll.request_history[-1].headers["Authorization"] == "Bearer t0k3n"
    assert clock.now == 1002.0


@pytest.mark.parametrize(
    "state, expected_error",
    [("PENDING", DatabricksWarehouseStarting), ("RUNNING", DatabricksTimeout)],
)
@pytest.mark.parametrize(
    "cancel_response",
    [
        {"json": {}},
        {"status_code": 404, "json": {"error_code": "RESOURCE_DOES_NOT_EXIST"}},
        {"status_code": 503, "text": "unavailable"},
        {"exc": requests.Timeout},
    ],
    ids=["cancelled", "already-closed", "server-error", "timeout"],
)
def test_run__deadline_reached__cancels_and_raises(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token: Any,
    state: str,
    expected_error: type[Exception],
    cancel_response: dict[str, Any],
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, json=_state(state))
    poll = requests_mock.get(f"{STATEMENTS_URL}/st-1", json=_state(state))
    cancel = requests_mock.post(f"{STATEMENTS_URL}/st-1/cancel", **cancel_response)

    # When
    with pytest.raises(expected_error):
        with databricks.databricks_session(
            databricks_connection, budget_seconds=5
        ) as session:
            session.run("SELECT 1", {})

    # Then
    assert poll.call_count == 5
    assert cancel.call_count == 1
    assert cancel.request_history[-1].headers["Authorization"] == "Bearer t0k3n"


def test_run__poll_held_open_while_starting__raises_starting(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token: Any,
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, json=_state("PENDING"))
    poll = requests_mock.get(f"{STATEMENTS_URL}/st-1", exc=requests.ReadTimeout)
    cancel = requests_mock.post(f"{STATEMENTS_URL}/st-1/cancel", json={})

    # When
    with pytest.raises(DatabricksWarehouseStarting):
        with databricks.databricks_session(
            databricks_connection, budget_seconds=5
        ) as session:
            session.run("SELECT 1", {})

    # Then
    assert poll.call_count == 5
    assert cancel.call_count == 1


def _multi_chunk() -> dict[str, Any]:
    payload = _succeeded([("event", "STRING")], [["purchase"]])
    payload["result"]["next_chunk_index"] = 1
    return payload


@pytest.mark.parametrize(
    "payload, expected_error_class",
    [
        (
            {
                "statement_id": "st-1",
                "status": {
                    "state": "FAILED",
                    "error": {
                        "error_code": "BAD_REQUEST",
                        "message": "[TABLE_OR_VIEW_NOT_FOUND] The table `events` cannot be found.",
                    },
                },
            },
            "TABLE_OR_VIEW_NOT_FOUND",
        ),
        (_multi_chunk(), "MULTI_CHUNK_RESULT"),
    ],
    ids=["failed", "multi-chunk"],
)
def test_run__unusable_result__raises_error_class(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token: Any,
    payload: dict[str, Any],
    expected_error_class: str,
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, json=payload)

    # When
    with pytest.raises(DatabricksRequestError) as exc_info:
        with databricks.databricks_session(
            databricks_connection, budget_seconds=5
        ) as session:
            session.run("SELECT event FROM events", {})

    # Then
    assert exc_info.value.error_class == expected_error_class


def test_run__redirect__is_not_followed(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    requests_mock.post(
        TOKEN_URL,
        status_code=302,
        headers={"Location": "http://169.254.169.254/latest"},
    )
    metadata = requests_mock.post("http://169.254.169.254/latest", json={})

    # When
    with pytest.raises(DatabricksRequestError) as exc_info:
        with databricks.databricks_session(databricks_connection, budget_seconds=5):
            pass  # pragma: no cover

    # Then
    assert exc_info.value.status_code == 302
    assert exc_info.value.error_class is None
    assert metadata.call_count == 0


@pytest.mark.parametrize(
    "token_response, expected_error",
    [
        ({"status_code": 400, "text": "nope"}, DatabricksAuthError),
        ({"status_code": 401, "text": "nope"}, DatabricksAuthError),
        ({"status_code": 503, "text": "nope"}, DatabricksRequestError),
        (
            {
                "status_code": 403,
                "json": {
                    "error": "access_denied",
                    "error_description": "Scopes 'sql' are not assigned to the client sp-id",
                },
            },
            DatabricksSecretScopeError,
        ),
    ],
    ids=["bad-request", "unauthorised", "server-error", "secret-scope"],
)
def test_databricks_session__token_rejected__raises(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token_response: dict[str, Any],
    expected_error: type[Exception],
) -> None:
    # Given
    requests_mock.post(TOKEN_URL, **token_response)

    # When / Then
    with pytest.raises(expected_error):
        with databricks.databricks_session(databricks_connection, budget_seconds=5):
            pass  # pragma: no cover


def test_run__typed_columns__converts_values(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token: Any,
) -> None:
    # Given
    columns = [
        ("big", "BIGINT"),
        ("int", "INT"),
        ("long", "LONG"),
        ("short", "SHORT"),
        ("double", "DOUBLE"),
        ("float", "FLOAT"),
        ("decimal", "DECIMAL"),
        ("yes", "BOOLEAN"),
        ("no", "BOOLEAN"),
        ("at_offset", "TIMESTAMP"),
        ("at_zulu", "TIMESTAMP"),
        ("text", "STRING"),
        ("missing", "STRING"),
    ]
    row: list[str | None] = [
        "1",
        "2",
        "3",
        "4",
        "1.5",
        "2.5",
        "3.25",
        "true",
        "false",
        "2026-01-01T10:00:00.000+02:00",
        "2026-01-01T08:00:00Z",
        "control",
        None,
    ]
    requests_mock.post(STATEMENTS_URL, json=_succeeded(columns, [row]))

    # When
    with databricks.databricks_session(
        databricks_connection, budget_seconds=5
    ) as session:
        rows, names = session.run("SELECT 1", {})

    # Then
    utc_eight = datetime(2026, 1, 1, 8, tzinfo=timezone.utc)
    assert rows == [
        [1, 2, 3, 4, 1.5, 2.5, 3.25, True, False, utc_eight, utc_eight, "control", None]
    ]
    assert [type(value) for value in rows[0][:7]] == [int] * 4 + [float] * 3
    bucket = rows[0][9]
    assert isinstance(bucket, datetime)
    assert bucket.isoformat() == "2026-01-01T08:00:00+00:00"
    assert names == [name for name, _type_name in columns]


def test_run__timestamp_without_offset__raises(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token: Any,
) -> None:
    # Given
    requests_mock.post(
        STATEMENTS_URL,
        json=_succeeded([("bucket", "TIMESTAMP")], [["2026-01-01T08:00:00"]]),
    )

    # When / Then
    with pytest.raises(ValueError, match="without an offset"):
        with databricks.databricks_session(
            databricks_connection, budget_seconds=5
        ) as session:
            session.run("SELECT 1", {})


def test_run__params__sends_only_referenced_typed_parameters(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token: Any,
) -> None:
    # Given
    statement = requests_mock.post(STATEMENTS_URL, json=_succeeded())
    window_start = datetime(2026, 1, 1, 2, tzinfo=timezone(timedelta(hours=2)))

    # When
    with databricks.databricks_session(
        databricks_connection, budget_seconds=5
    ) as session:
        session.run(
            "SELECT :event_1, :limit, :window_start",
            {
                "event_1": "purchase",
                "event_10": "signup",
                "limit": 501,
                "window_start": window_start,
                "unused": "x",
            },
        )

    # Then
    assert statement.request_history[-1].json()["parameters"] == [
        {"name": "event_1", "value": "purchase", "type": "STRING"},
        {"name": "limit", "value": "501", "type": "INT"},
        {
            "name": "window_start",
            "value": "2026-01-01T00:00:00+00:00",
            "type": "TIMESTAMP",
        },
    ]


@pytest.mark.parametrize(
    "value, expected_error",
    [
        (datetime(2026, 1, 1), ValueError),
        (True, TypeError),
        (1.5, TypeError),
    ],
    ids=["naive-datetime", "bool", "float"],
)
def test_run__unsupported_param__raises(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token: Any,
    value: object,
    expected_error: type[Exception],
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, json=_succeeded())

    # When / Then
    with pytest.raises(expected_error):
        with databricks.databricks_session(
            databricks_connection, budget_seconds=5
        ) as session:
            session.run("SELECT :value", {"value": value})


@pytest.mark.parametrize(
    "error, expected_detail",
    [
        (
            DeliveryConfigError("Stored connection details are incomplete."),
            "Stored connection details are incomplete.",
        ),
        (DatabricksAuthError(), "Authentication failed."),
        (
            DatabricksSecretScopeError(),
            "The service principal secret must allow the sql scope. "
            "Generate a new secret with the sql scope.",
        ),
        (
            DatabricksWarehouseStarting(),
            "The SQL warehouse is starting. Test the connection again in a few minutes.",
        ),
        (requests.ConnectionError(), "Could not connect to the host."),
        (DatabricksTimeout(), "Could not connect to the host."),
        (DatabricksRequestError(401, None), "Authentication failed."),
        (DatabricksRequestError(403, None), "Authentication failed."),
        (
            DatabricksRequestError(403, "PERMISSION_DENIED"),
            "The Databricks workspace rejected the request.",
        ),
        (
            DatabricksRequestError(None, "TABLE_OR_VIEW_NOT_FOUND"),
            "Events table not found in the configured database. Run the setup SQL to create it.",
        ),
        (DatabricksRequestError(None, "SCHEMA_NOT_FOUND"), "Database does not exist."),
        (
            DatabricksRequestError(None, "NO_SUCH_CATALOG_EXCEPTION"),
            "Database does not exist.",
        ),
        (DatabricksRequestError(404, None), "SQL warehouse not found."),
        (
            DatabricksRequestError(400, "RESOURCE_DOES_NOT_EXIST"),
            "SQL warehouse not found.",
        ),
        (
            DatabricksRequestError(400, "INVALID_PARAMETER_VALUE"),
            "The Databricks workspace rejected the request.",
        ),
        (RuntimeError("raw driver detail"), "Connection failed."),
    ],
)
def test_describe_databricks_error__error__returns_user_facing_detail(
    error: Exception,
    expected_detail: str,
) -> None:
    # When
    detail = databricks.describe_databricks_error(error)

    # Then
    assert detail == expected_detail
