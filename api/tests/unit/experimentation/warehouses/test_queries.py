from datetime import datetime, timezone
from typing import Any, Literal
from unittest.mock import MagicMock, call

import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from experimentation.dataclasses import MetricSpec
from experimentation.models import MetricAggregation, WarehouseConnection
from experimentation.types import ExposureGranularity
from experimentation.warehouses.base import Warehouse
from experimentation.warehouses.clickhouse import ClickHouseWarehouse
from experimentation.warehouses.flagsmith import FlagsmithWarehouse

Provider = Literal["customer", "managed"]

WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 8, tzinfo=timezone.utc)

EVENT_NAMES_SQL = (
    "SELECT event FROM events WHERE environment_key = %(environment_key)s "
    "GROUP BY event ORDER BY max(timestamp) DESC LIMIT %(limit)s"
)
EVENT_STATS_SQL = (
    "SELECT count() AS total, uniqExact(event) AS unique "
    "FROM events WHERE environment_key = %(environment_key)s"
)

EXPOSURES_CTE_SQL = """
WITH exposures AS (
    SELECT
        identifier,
        if(uniqExact(value) > 1, '', any(value)) AS variant,
        uniqExact(value) > 1 AS quarantined,
        min(timestamp) AS first_exposure
    FROM events
    WHERE environment_key = %(environment_key)s
        AND event = %(exposure_event)s
        AND feature_name = %(feature_name)s
        AND timestamp >= %(window_start)s
        AND timestamp < %(window_end)s
    GROUP BY identifier
)"""

EXPOSURE_BUCKETS_HOUR_SQL = (
    EXPOSURES_CTE_SQL
    + """
SELECT
    quarantined,
    variant,
    toStartOfHour(first_exposure, 'UTC') AS bucket,
    count() AS first_exposed_identities
FROM exposures
GROUP BY quarantined, variant, bucket
ORDER BY bucket
"""
)

EXPOSURE_BUCKETS_DAY_SQL = EXPOSURE_BUCKETS_HOUR_SQL.replace(
    "toStartOfHour", "toStartOfDay"
)

RESULTS_NO_METRICS_SQL = (
    EXPOSURES_CTE_SQL
    + """
SELECT variant, count() AS n
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
        countIf(m.event = %(metric_0_event)s AND m.timestamp >= e.first_exposure) > 0 AS m0,
        countIf(m.event = %(metric_1_event)s AND m.timestamp >= e.first_exposure) AS m1,
        sumIf(toFloat64OrZero(m.value), m.event = %(metric_2_event)s AND m.timestamp >= e.first_exposure) AS m2,
        if(countIf(m.event = %(metric_3_event)s AND m.timestamp >= e.first_exposure) > 0, avgIf(toFloat64OrZero(m.value), m.event = %(metric_3_event)s AND m.timestamp >= e.first_exposure), 0) AS m3,
        countIf(m.event = %(metric_4_event)s AND m.timestamp >= e.first_exposure) > 0 AS m4
    FROM exposures AS e
    LEFT JOIN events AS m
        ON m.identifier = e.identifier
        AND m.environment_key = %(environment_key)s
        AND m.event IN %(metric_events)s
        AND m.timestamp >= %(window_start)s
        AND m.timestamp < %(window_end)s
    WHERE e.quarantined = 0
    GROUP BY e.identifier, e.variant
)
SELECT variant, count() AS n,
    sum(m0) AS m0_sum, sum(m0 * m0) AS m0_sum_squares,
    sum(m1) AS m1_sum, sum(m1 * m1) AS m1_sum_squares,
    sum(m2) AS m2_sum, sum(m2 * m2) AS m2_sum_squares,
    sum(m3) AS m3_sum, sum(m3 * m3) AS m3_sum_squares,
    sum(m4) AS m4_sum, sum(m4 * m4) AS m4_sum_squares
FROM unit_values
GROUP BY variant"""
)

CONVERSIONS_HOUR_SQL = (
    EXPOSURES_CTE_SQL
    + """,
first_conversions AS (
    SELECT
        e.variant AS variant,
        minIfOrNull(m.timestamp, m.event = %(metric_0_event)s AND m.timestamp >= e.first_exposure) AS c0,
        minIfOrNull(m.timestamp, m.event = %(metric_4_event)s AND m.timestamp >= e.first_exposure) AS c4
    FROM exposures AS e
    LEFT JOIN events AS m
        ON m.identifier = e.identifier
        AND m.environment_key = %(environment_key)s
        AND m.event IN %(conversion_events)s
        AND m.timestamp >= %(window_start)s
        AND m.timestamp < %(window_end)s
    WHERE e.quarantined = 0
    GROUP BY e.identifier, e.variant
)
SELECT
    variant,
    metric_index,
    toStartOfHour(first_conversion, 'UTC') AS bucket,
    count() AS converted_identities
FROM first_conversions
ARRAY JOIN [0, 4] AS metric_index, [c0, c4] AS first_conversion
WHERE first_conversion IS NOT NULL
GROUP BY variant, metric_index, bucket
ORDER BY bucket"""
)

WINDOW_PARAMS: dict[str, object] = {
    "environment_key": "env-key",
    "exposure_event": "$flag_exposure",
    "feature_name": "checkout_flow",
    "window_start": datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
    "window_end": datetime(2026, 1, 8, 0, 0, tzinfo=timezone.utc),
}

METRIC_PARAMS: dict[str, object] = {
    **WINDOW_PARAMS,
    "metric_events": ["purchase", "page_view", "revenue", "basket_size", "signup"],
    "conversion_events": ["purchase", "signup"],
    "metric_0_event": "purchase",
    "metric_1_event": "page_view",
    "metric_2_event": "revenue",
    "metric_3_event": "basket_size",
    "metric_4_event": "signup",
}

SPECS = [
    MetricSpec(11, "purchase", MetricAggregation.OCCURRENCE, False),
    MetricSpec(12, "page_view", MetricAggregation.COUNT, False),
    MetricSpec(13, "revenue", MetricAggregation.SUM, False),
    MetricSpec(14, "basket_size", MetricAggregation.MEAN, True),
    MetricSpec(15, "signup", MetricAggregation.OCCURRENCE, False),
]


@pytest.fixture(params=["customer", "managed"])
def provider(request: pytest.FixtureRequest) -> Provider:
    value: Provider = request.param
    return value


@pytest.fixture()
def target(
    provider: Provider,
    request: pytest.FixtureRequest,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> tuple[Warehouse, WarehouseConnection, MagicMock]:
    if provider == "customer":
        client = mocker.patch(
            "experimentation.warehouses.clickhouse.clickhouse_connect.get_client",
        ).return_value
        client.query.return_value = mocker.Mock(result_rows=[], column_names=[])
        return (
            ClickHouseWarehouse(),
            request.getfixturevalue("clickhouse_connection"),
            client.query,
        )
    settings.EXPERIMENTATION_CLICKHOUSE_URL = "clickhouse://ch.example.com/db"
    client = mocker.patch("experimentation.warehouses.flagsmith.Client").return_value
    client.execute.side_effect = lambda query, params, **kwargs: (
        ([], []) if kwargs.get("with_column_types") else []
    )
    return (
        FlagsmithWarehouse(),
        request.getfixturevalue("warehouse_connection"),
        client.execute,
    )


def _lookup_call(provider: Provider, sql: str, params: dict[str, object]) -> Any:
    if provider == "customer":
        return call(sql, parameters=params)
    return call(sql, params)


def _read_call(provider: Provider, sql: str, params: dict[str, object]) -> Any:
    if provider == "customer":
        return call(
            sql,
            parameters=params,
            settings={"join_use_nulls": 0, "aggregate_functions_null_for_empty": 0},
            tz_mode="aware",
        )
    return call(sql, params, with_column_types=True)


def test_get_event_names__any_provider__sends_expected_sql(
    provider: Provider,
    target: tuple[Warehouse, WarehouseConnection, MagicMock],
    reset_cache: None,
) -> None:
    # Given
    warehouse, connection, run = target

    # When
    warehouse.get_event_names(connection, "env-key")

    # Then
    assert run.call_args_list == [
        _lookup_call(
            provider, EVENT_NAMES_SQL, {"environment_key": "env-key", "limit": 501}
        )
    ]


def test_get_event_stats__any_provider__sends_expected_sql(
    provider: Provider,
    target: tuple[Warehouse, WarehouseConnection, MagicMock],
    reset_cache: None,
) -> None:
    # Given
    warehouse, connection, run = target

    # When
    warehouse.get_event_stats(connection, "env-key")

    # Then
    assert run.call_args_list == [
        _lookup_call(provider, EVENT_STATS_SQL, {"environment_key": "env-key"})
    ]


@pytest.mark.parametrize(
    "granularity, expected_sql",
    [("hour", EXPOSURE_BUCKETS_HOUR_SQL), ("day", EXPOSURE_BUCKETS_DAY_SQL)],
    ids=["hour", "day"],
)
def test_get_exposure_buckets__granularity__sends_expected_sql(
    provider: Provider,
    target: tuple[Warehouse, WarehouseConnection, MagicMock],
    granularity: ExposureGranularity,
    expected_sql: str,
) -> None:
    # Given
    warehouse, connection, run = target

    # When
    warehouse.get_exposure_buckets(
        connection,
        environment_key="env-key",
        feature_name="checkout_flow",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        granularity=granularity,
    )

    # Then
    assert run.call_args_list == [_read_call(provider, expected_sql, WINDOW_PARAMS)]


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
                (RESULTS_SQL, METRIC_PARAMS),
                (CONVERSIONS_HOUR_SQL, METRIC_PARAMS),
                (EXPOSURE_BUCKETS_HOUR_SQL, WINDOW_PARAMS),
            ],
        ),
    ],
    ids=["no-metrics", "every-aggregation"],
)
def test_get_results_aggregates__specs__sends_expected_sql(
    provider: Provider,
    target: tuple[Warehouse, WarehouseConnection, MagicMock],
    specs: list[MetricSpec],
    expected: list[tuple[str, dict[str, object]]],
) -> None:
    # Given
    warehouse, connection, run = target

    # When
    warehouse.get_results_aggregates(
        connection,
        environment_key="env-key",
        feature_name="checkout_flow",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        specs=specs,
        granularity="hour",
    )

    # Then
    assert run.call_args_list == [
        _read_call(provider, sql, params) for sql, params in expected
    ]
