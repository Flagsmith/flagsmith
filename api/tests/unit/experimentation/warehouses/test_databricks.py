from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from requests_mock import Mocker as RequestsMockerFixture
from rest_framework import serializers

from experimentation.dataclasses import (
    MetricSpec,
    WarehouseEventNames,
    WarehouseEventStats,
)
from experimentation.models import MetricAggregation, WarehouseConnection
from experimentation.types import ExposureGranularity
from experimentation.warehouses import databricks
from experimentation.warehouses.databricks import (
    DatabricksAuthError,
    DatabricksRequestError,
    DatabricksSecretScopeError,
    DatabricksTimeout,
    DatabricksWarehouse,
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

WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 8, tzinfo=timezone.utc)

EVENT_NAMES_SQL = (
    "SELECT event FROM events WHERE environment_key = :environment_key "
    "GROUP BY event ORDER BY max(timestamp) DESC LIMIT :limit"
)
EVENT_STATS_SQL = (
    "SELECT count(*) AS total, count(DISTINCT event) AS unique "
    "FROM events WHERE environment_key = :environment_key"
)

EXPOSURES_CTE_SQL = """
WITH exposures AS (
    SELECT
        identifier,
        if(count(DISTINCT value) > 1, '', any_value(value)) AS variant,
        CAST(count(DISTINCT value) > 1 AS INT) AS quarantined,
        min(timestamp) AS first_exposure
    FROM events
    WHERE environment_key = :environment_key
        AND event = :exposure_event
        AND feature_name = :feature_name
        AND timestamp >= :window_start
        AND timestamp < :window_end
    GROUP BY identifier
)"""

EXPOSURE_BUCKETS_HOUR_SQL = (
    EXPOSURES_CTE_SQL
    + """
SELECT
    quarantined,
    variant,
    timestamp_seconds(floor(unix_seconds(first_exposure) / 3600) * 3600) AS bucket,
    count(*) AS first_exposed_identities
FROM exposures
GROUP BY quarantined, variant, bucket
ORDER BY bucket
"""
)

EXPOSURE_BUCKETS_DAY_SQL = EXPOSURE_BUCKETS_HOUR_SQL.replace(
    "/ 3600) * 3600", "/ 86400) * 86400"
)

RESULTS_NO_METRICS_SQL = (
    EXPOSURES_CTE_SQL
    + """
SELECT variant, count(*) AS n
FROM exposures
WHERE quarantined = 0
GROUP BY variant"""
)

RESULTS_SQL = (
    EXPOSURES_CTE_SQL
    + """,
unit_values AS (
    SELECT
        e.variant AS variant,
        CAST(count_if(m.event = :metric_0_event AND m.timestamp >= e.first_exposure) > 0 AS INT) AS m0,
        count_if(m.event = :metric_1_event AND m.timestamp >= e.first_exposure) AS m1,
        coalesce(sum(CASE WHEN m.event = :metric_2_event AND m.timestamp >= e.first_exposure THEN coalesce(try_cast(m.value AS DOUBLE), 0) END), 0) AS m2,
        coalesce(avg(CASE WHEN m.event = :metric_3_event AND m.timestamp >= e.first_exposure THEN coalesce(try_cast(m.value AS DOUBLE), 0) END), 0) AS m3,
        CAST(count_if(m.event = :metric_4_event AND m.timestamp >= e.first_exposure) > 0 AS INT) AS m4
    FROM exposures AS e
    LEFT JOIN events AS m
        ON m.identifier = e.identifier
        AND m.environment_key = :environment_key
        AND m.event IN (:metric_events_0, :metric_events_1, :metric_events_2, :metric_events_3, :metric_events_4)
        AND m.timestamp >= :window_start
        AND m.timestamp < :window_end
    WHERE e.quarantined = 0
    GROUP BY e.identifier, e.variant
)
SELECT variant, count(*) AS n,
    sum(m0) AS m0_sum, sum(m0 * m0) AS m0_sum_squares,
    sum(m1) AS m1_sum, sum(m1 * m1) AS m1_sum_squares,
    sum(m2) AS m2_sum, sum(m2 * m2) AS m2_sum_squares,
    sum(m3) AS m3_sum, sum(m3 * m3) AS m3_sum_squares,
    sum(m4) AS m4_sum, sum(m4 * m4) AS m4_sum_squares
FROM unit_values
GROUP BY variant"""
)

FIRST_CONVERSIONS_SQL = (
    EXPOSURES_CTE_SQL
    + """,
first_conversions AS (
    SELECT
        e.variant AS variant,
        min(CASE WHEN m.event = :metric_0_event AND m.timestamp >= e.first_exposure THEN m.timestamp END) AS c0,
        min(CASE WHEN m.event = :metric_4_event AND m.timestamp >= e.first_exposure THEN m.timestamp END) AS c4
    FROM exposures AS e
    LEFT JOIN events AS m
        ON m.identifier = e.identifier
        AND m.environment_key = :environment_key
        AND m.event IN (:conversion_events_0, :conversion_events_1)
        AND m.timestamp >= :window_start
        AND m.timestamp < :window_end
    WHERE e.quarantined = 0
    GROUP BY e.identifier, e.variant
)
SELECT
    variant,
    metric_index,
"""
)

CONVERSIONS_HOUR_SQL = (
    FIRST_CONVERSIONS_SQL
    + """    timestamp_seconds(floor(unix_seconds(first_conversion) / 3600) * 3600) AS bucket,
    count(*) AS converted_identities
FROM first_conversions
LATERAL VIEW inline(arrays_zip(array(0, 4), array(c0, c4))) AS metric_index, first_conversion
WHERE first_conversion IS NOT NULL
GROUP BY variant, metric_index, bucket
ORDER BY bucket"""
)

WINDOW_PARAMS = [
    {"name": "environment_key", "value": "env-key", "type": "STRING"},
    {"name": "exposure_event", "value": "$flag_exposure", "type": "STRING"},
    {"name": "feature_name", "value": "checkout_flow", "type": "STRING"},
    {"name": "window_start", "value": "2026-01-01T00:00:00+00:00", "type": "TIMESTAMP"},
    {"name": "window_end", "value": "2026-01-08T00:00:00+00:00", "type": "TIMESTAMP"},
]

RESULTS_PARAMS = [
    *WINDOW_PARAMS,
    {"name": "metric_events_0", "value": "purchase", "type": "STRING"},
    {"name": "metric_events_1", "value": "page_view", "type": "STRING"},
    {"name": "metric_events_2", "value": "revenue", "type": "STRING"},
    {"name": "metric_events_3", "value": "basket_size", "type": "STRING"},
    {"name": "metric_events_4", "value": "signup", "type": "STRING"},
    {"name": "metric_0_event", "value": "purchase", "type": "STRING"},
    {"name": "metric_1_event", "value": "page_view", "type": "STRING"},
    {"name": "metric_2_event", "value": "revenue", "type": "STRING"},
    {"name": "metric_3_event", "value": "basket_size", "type": "STRING"},
    {"name": "metric_4_event", "value": "signup", "type": "STRING"},
]

CONVERSIONS_PARAMS = [
    *WINDOW_PARAMS,
    {"name": "conversion_events_0", "value": "purchase", "type": "STRING"},
    {"name": "conversion_events_1", "value": "signup", "type": "STRING"},
    {"name": "metric_0_event", "value": "purchase", "type": "STRING"},
    {"name": "metric_4_event", "value": "signup", "type": "STRING"},
]

SPECS = [
    MetricSpec(11, "purchase", MetricAggregation.OCCURRENCE, False),
    MetricSpec(12, "page_view", MetricAggregation.COUNT, False),
    MetricSpec(13, "revenue", MetricAggregation.SUM, False),
    MetricSpec(14, "basket_size", MetricAggregation.MEAN, True),
    MetricSpec(15, "signup", MetricAggregation.OCCURRENCE, False),
]


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
        headers={"x-databricks-org-id": "1234567890"},
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


def _body(sql: str, parameters: list[dict[str, str]], wait: str) -> dict[str, Any]:
    return {
        "warehouse_id": "abc123",
        "catalog": "main",
        "schema": "flagsmith_exp",
        "statement": sql,
        "parameters": parameters,
        "wait_timeout": wait,
        "on_wait_timeout": "CONTINUE",
        "disposition": "INLINE",
        "format": "JSON_ARRAY",
    }


def _sent(requests_mock: RequestsMockerFixture) -> list[Any]:
    return [
        request.json() if request.path.startswith("/api/") else request.path
        for request in requests_mock.request_history
    ]


@pytest.fixture()
def statements(requests_mock: RequestsMockerFixture) -> Any:
    return requests_mock.post(STATEMENTS_URL, json=_succeeded())


@pytest.mark.parametrize(
    "overrides",
    [
        {"host": "Acme.Cloud.Databricks.com", "region": " US-East-1 "},
        {
            "host": "https://acme.cloud.databricks.com/",
            "warehouse_id": "/sql/1.0/warehouses/abc123",
        },
        {
            "host": " https://acme.cloud.databricks.com/sql/editor?o=1234567890 ",
            "workspace_id": "",
            "warehouse_id": "abc123/",
        },
    ],
    ids=["mixed-case", "pasted-url-and-http-path", "workspace-id-from-pasted-url"],
)
def test_validate_config__valid__normalises_and_applies_defaults(
    overrides: dict[str, str],
) -> None:
    # Given
    config = {**VALID_CONFIG, **overrides}

    # When
    result = DatabricksWarehouse().validate_config(config)

    # Then
    assert result == {
        "host": "acme.cloud.databricks.com",
        "workspace_id": "1234567890",
        "region": "us-east-1",
        "warehouse_id": "abc123",
        "catalog": "main",
        "schema": "flagsmith_exp",
    }


def test_validate_config__stored__merges_over_stored() -> None:
    # Given
    stored = {**VALID_CONFIG, "schema": "events_db"}

    # When
    result = DatabricksWarehouse().validate_config({"catalog": "prod"}, stored=stored)

    # Then
    assert result == {**stored, "catalog": "prod"}


@pytest.mark.parametrize(
    "config, expected_errors",
    [
        ("not-a-dict", {"config": "Must be an object."}),
        ({**VALID_CONFIG, "token": "x"}, {"config": {"token": "Unknown field."}}),
        (
            {**VALID_CONFIG, "host": ""},
            {"config": {"host": "This field is required."}},
        ),
        *(
            (
                {**VALID_CONFIG, "host": host},
                {"config": {"host": "Enter a Databricks workspace hostname."}},
            )
            for host in (
                "https://acme.example.com/",
                "https://evil.example/acme.cloud.databricks.com",
                "acme.cloud.databricks.com:443",
                "acme.cloud.databricks.com.",
                "-acme.cloud.databricks.com",
                "acme.cloud.databricks.com.evil.example",
            )
        ),
        *(
            (
                {**VALID_CONFIG, "workspace_id": workspace_id},
                {"config": {"workspace_id": "Enter the numeric workspace ID."}},
            )
            for workspace_id in ("", "dbc-1234", 1)
        ),
        *(
            (
                {**VALID_CONFIG, "region": region},
                {"config": {"region": "Enter the workspace region, e.g. us-east-1."}},
            )
            for region in ("", "us_east_1", 1)
        ),
        (
            {**VALID_CONFIG, "warehouse_id": "abc-123"},
            {"config": {"warehouse_id": "Enter a valid identifier."}},
        ),
        (
            {**VALID_CONFIG, "warehouse_id": 1},
            {"config": {"warehouse_id": "Enter a valid identifier."}},
        ),
        (
            {**VALID_CONFIG, "catalog": ""},
            {"config": {"catalog": "Enter a valid identifier."}},
        ),
        (
            {**VALID_CONFIG, "catalog": 1},
            {"config": {"catalog": "Enter a valid identifier."}},
        ),
        (
            {**VALID_CONFIG, "schema": "flagsmith.exp"},
            {"config": {"schema": "Enter a valid identifier."}},
        ),
    ],
)
def test_validate_config__invalid__raises_validation_error(
    config: Any,
    expected_errors: dict[str, Any],
) -> None:
    # Given
    warehouse = DatabricksWarehouse()

    # When
    with pytest.raises(serializers.ValidationError) as exc_info:
        warehouse.validate_config(config)

    # Then
    assert exc_info.value.detail == expected_errors


def test_validate_config__internal_host__raises_validation_error(
    is_internal_address: MagicMock,
) -> None:
    # Given
    is_internal_address.return_value = True

    # When
    with pytest.raises(serializers.ValidationError) as exc_info:
        DatabricksWarehouse().validate_config(VALID_CONFIG)

    # Then
    assert exc_info.value.detail == {
        "config": {
            "host": "Host must not target internal or private network addresses."
        }
    }
    is_internal_address.assert_called_once_with(
        "acme.cloud.databricks.com", include_shared=True
    )


def test_validate_credentials__valid__returns_client_credentials() -> None:
    # Given
    credentials = {"client_id": "sp-id", "client_secret": "sp-secret"}

    # When
    result = DatabricksWarehouse().validate_credentials(credentials)

    # Then
    assert result == credentials


@pytest.mark.parametrize(
    "credentials, expected_errors",
    [
        ("not-a-dict", {"credentials": "Must be an object."}),
        (
            {"client_secret": "sp-secret"},
            {"credentials": {"client_id": "This field is required."}},
        ),
        (
            {"client_id": "sp-id", "client_secret": ""},
            {"credentials": {"client_secret": "This field is required."}},
        ),
        (
            {"client_id": 1, "client_secret": "sp-secret"},
            {"credentials": {"client_id": "This field is required."}},
        ),
    ],
)
def test_validate_credentials__invalid__raises_validation_error(
    credentials: Any,
    expected_errors: dict[str, Any],
) -> None:
    # Given
    warehouse = DatabricksWarehouse()

    # When
    with pytest.raises(serializers.ValidationError) as exc_info:
        warehouse.validate_credentials(credentials)

    # Then
    assert exc_info.value.detail == expected_errors


def test_verify__reachable__probes_events_table_with_one_token(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token: Any,
) -> None:
    # Given
    statement = requests_mock.post(STATEMENTS_URL, json=_succeeded())

    # When
    DatabricksWarehouse().verify(databricks_connection)

    # Then
    assert token.call_count == 1
    assert token.request_history[-1].headers["Authorization"] == (
        "Basic c3AtaWQ6c3Atc2VjcmV0"
    )
    assert token.request_history[-1].text == "grant_type=client_credentials&scope=sql"
    assert statement.request_history[-1].headers["Authorization"] == "Bearer t0k3n"
    assert statement.request_history[-1].json() == _body(
        "SELECT 1 FROM events LIMIT 0", [], "5s"
    )


@pytest.mark.parametrize(
    "token_response, statement_response, expected_detail",
    [
        (
            {"status_code": 401, "json": {"error": "invalid_client"}},
            None,
            "Authentication failed.",
        ),
        (
            {"exc": requests.ConnectionError},
            None,
            "Could not connect to the host.",
        ),
        (
            {"json": {"access_token": "t0k3n"}},
            {
                "status_code": 404,
                "json": {
                    "error_code": "RESOURCE_DOES_NOT_EXIST",
                    "message": "Warehouse abc123 does not exist.",
                },
            },
            "SQL warehouse not found.",
        ),
        (
            {
                "json": {"access_token": "t0k3n"},
                "headers": {"x-databricks-org-id": "999"},
            },
            None,
            "The workspace ID does not match this workspace.",
        ),
    ],
    ids=[
        "unauthorised",
        "unreachable",
        "missing-warehouse",
        "workspace-mismatch",
    ],
)
def test_verify__failure__raises_described_error(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token_response: dict[str, Any],
    statement_response: dict[str, Any] | None,
    expected_detail: str,
) -> None:
    # Given
    requests_mock.post(TOKEN_URL, **token_response)
    if statement_response is not None:
        requests_mock.post(STATEMENTS_URL, **statement_response)
    warehouse = DatabricksWarehouse()

    # When
    with pytest.raises(Exception) as exc_info:
        warehouse.verify(databricks_connection)

    # Then
    assert warehouse.describe_error(exc_info.value) == expected_detail


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
    # Given / When
    detail = databricks.describe_databricks_error(error)

    # Then
    assert detail == expected_detail


@pytest.mark.parametrize(
    "method, statement_response, expected_body, expected",
    [
        (
            "get_event_names",
            _succeeded([("event", "STRING")], [["purchase"], ["signup"]]),
            _body(
                EVENT_NAMES_SQL,
                [
                    {"name": "environment_key", "value": "env-key", "type": "STRING"},
                    {"name": "limit", "value": "501", "type": "INT"},
                ],
                "15s",
            ),
            WarehouseEventNames(events=["purchase", "signup"], is_truncated=False),
        ),
        (
            "get_event_stats",
            _succeeded([("total", "BIGINT"), ("unique", "BIGINT")], [["10", "2"]]),
            _body(
                EVENT_STATS_SQL,
                [{"name": "environment_key", "value": "env-key", "type": "STRING"}],
                "5s",
            ),
            WarehouseEventStats(total_events_received=10, unique_events_count=2),
        ),
    ],
)
def test_event_lookup__reachable__sends_expected_sql_and_caches(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    reset_cache: None,
    token: Any,
    method: str,
    statement_response: dict[str, Any],
    expected_body: dict[str, Any],
    expected: object,
) -> None:
    # Given
    requests_mock.post(STATEMENTS_URL, json=statement_response)
    lookup = getattr(DatabricksWarehouse(), method)

    # When
    first = lookup(databricks_connection, "env-key")
    second = lookup(databricks_connection, "env-key")

    # Then
    assert first == second == expected
    assert _sent(requests_mock) == ["/oidc/v1/token", expected_body]


@pytest.mark.parametrize(
    "method, kind",
    [("get_event_names", "event_names"), ("get_event_stats", "event_stats")],
)
def test_event_lookup__unreachable__caches_unavailable_and_logs(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    reset_cache: None,
    log: StructuredLogCapture,
    method: str,
    kind: str,
) -> None:
    # Given
    token = requests_mock.post(TOKEN_URL, exc=requests.ConnectionError)
    lookup = getattr(DatabricksWarehouse(), method)

    # When
    first = lookup(databricks_connection, "env-key")
    second = lookup(databricks_connection, "env-key")

    # Then
    assert first is second is None
    assert token.call_count == 1
    assert [event["event"] for event in log.events] == [f"connection.{kind}_failed"]
    assert log.events[0]["environment__id"] == databricks_connection.environment_id


@pytest.mark.parametrize(
    "granularity, expected_sql",
    [("hour", EXPOSURE_BUCKETS_HOUR_SQL), ("day", EXPOSURE_BUCKETS_DAY_SQL)],
    ids=["hour", "day"],
)
def test_get_exposure_buckets__databricks__sends_expected_sql(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token: Any,
    statements: Any,
    granularity: ExposureGranularity,
    expected_sql: str,
) -> None:
    # Given
    warehouse = DatabricksWarehouse()

    # When
    warehouse.get_exposure_buckets(
        databricks_connection,
        environment_key="env-key",
        feature_name="checkout_flow",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        granularity=granularity,
    )

    # Then
    assert _sent(requests_mock) == [
        "/oidc/v1/token",
        _body(expected_sql, WINDOW_PARAMS, "30s"),
    ]


@pytest.mark.parametrize(
    "specs, expected",
    [
        (
            [],
            [
                (RESULTS_NO_METRICS_SQL, WINDOW_PARAMS),
                (EXPOSURE_BUCKETS_HOUR_SQL, WINDOW_PARAMS),
            ],
        ),
        (
            SPECS,
            [
                (RESULTS_SQL, RESULTS_PARAMS),
                (CONVERSIONS_HOUR_SQL, CONVERSIONS_PARAMS),
                (EXPOSURE_BUCKETS_HOUR_SQL, WINDOW_PARAMS),
            ],
        ),
    ],
    ids=["no-metrics", "every-aggregation"],
)
def test_get_results_aggregates__databricks__sends_expected_sql_with_one_token(
    databricks_connection: WarehouseConnection,
    requests_mock: RequestsMockerFixture,
    token: Any,
    statements: Any,
    specs: list[MetricSpec],
    expected: list[tuple[str, list[dict[str, str]]]],
) -> None:
    # Given
    warehouse = DatabricksWarehouse()

    # When
    warehouse.get_results_aggregates(
        databricks_connection,
        environment_key="env-key",
        feature_name="checkout_flow",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        specs=specs,
        granularity="hour",
    )

    # Then
    assert _sent(requests_mock) == [
        "/oidc/v1/token",
        *(_body(sql, parameters, "30s") for sql, parameters in expected),
    ]
