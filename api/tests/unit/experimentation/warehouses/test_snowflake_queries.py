from collections.abc import Callable
from datetime import datetime, timezone
from functools import partial

import pytest

from experimentation.dataclasses import MetricSpec
from experimentation.models import MetricAggregation
from experimentation.results_query import ResultsQueryBuilder
from experimentation.warehouses.dialect import SNOWFLAKE_DIALECT
from experimentation.warehouses.queries import (
    event_names_query,
    event_stats_query,
    exposure_buckets_query,
)

WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 8, tzinfo=timezone.utc)

SPECS = [
    MetricSpec(11, "purchase", MetricAggregation.OCCURRENCE, False),
    MetricSpec(12, "page_view", MetricAggregation.COUNT, False),
    MetricSpec(13, "revenue", MetricAggregation.SUM, False),
    MetricSpec(14, "basket_size", MetricAggregation.MEAN, True),
    MetricSpec(15, "signup", MetricAggregation.OCCURRENCE, False),
]

EVENT_NAMES_SQL = (
    "SELECT event FROM events WHERE environment_key = %(environment_key)s "
    "GROUP BY event ORDER BY max(timestamp) DESC LIMIT %(limit)s"
)
EVENT_STATS_SQL = (
    "SELECT count(*) AS total, count(DISTINCT event) AS unique_events, "
    "max(timestamp) AS last_event_at "
    "FROM events WHERE environment_key = %(environment_key)s"
)

EXPOSURES_CTE_SQL = """
WITH exposures AS (
    SELECT
        identifier,
        CASE WHEN count(DISTINCT coalesce(value, '')) > 1 THEN '' ELSE any_value(coalesce(value, '')) END AS variant,
        iff(count(DISTINCT coalesce(value, '')) > 1, 1, 0) AS quarantined,
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
    date_trunc('hour', first_exposure) AS bucket,
    count(*) AS first_exposed_identities
FROM exposures
GROUP BY quarantined, variant, bucket
ORDER BY bucket
"""
)

EXPOSURE_BUCKETS_DAY_SQL = EXPOSURE_BUCKETS_HOUR_SQL.replace(
    "date_trunc('hour'", "date_trunc('day'"
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
        iff(coalesce(count_if(m.event = %(metric_0_event)s AND m.timestamp >= e.first_exposure), 0) > 0, 1, 0) AS m0,
        coalesce(count_if(m.event = %(metric_1_event)s AND m.timestamp >= e.first_exposure), 0) AS m1,
        coalesce(sum(iff(m.event = %(metric_2_event)s AND m.timestamp >= e.first_exposure, iff(regexp_like(m.value, '^[-+]?([0-9]{1,30}([.][0-9]{0,30})?|[.][0-9]{1,30})([eE][-+]?[0-9]{1,2})?$'), try_to_double(m.value), 0), NULL)), 0) AS m2,
        coalesce(avg(iff(m.event = %(metric_3_event)s AND m.timestamp >= e.first_exposure, iff(regexp_like(m.value, '^[-+]?([0-9]{1,30}([.][0-9]{0,30})?|[.][0-9]{1,30})([eE][-+]?[0-9]{1,2})?$'), try_to_double(m.value), 0), NULL)), 0) AS m3,
        iff(coalesce(count_if(m.event = %(metric_4_event)s AND m.timestamp >= e.first_exposure), 0) > 0, 1, 0) AS m4
    FROM exposures AS e
    LEFT JOIN events AS m
        ON m.identifier = e.identifier
        AND m.environment_key = %(environment_key)s
        AND m.event IN (%(metric_events_0)s, %(metric_events_1)s, %(metric_events_2)s, %(metric_events_3)s, %(metric_events_4)s)
        AND m.timestamp >= %(window_start)s
        AND m.timestamp < %(window_end)s
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

CONVERSIONS_HOUR_SQL = (
    EXPOSURES_CTE_SQL
    + """,
first_conversions AS (
    SELECT
        e.variant AS variant,
        min(iff(m.event = %(metric_0_event)s AND m.timestamp >= e.first_exposure, m.timestamp, NULL)) AS c0,
        min(iff(m.event = %(metric_4_event)s AND m.timestamp >= e.first_exposure, m.timestamp, NULL)) AS c4
    FROM exposures AS e
    LEFT JOIN events AS m
        ON m.identifier = e.identifier
        AND m.environment_key = %(environment_key)s
        AND m.event IN (%(conversion_events_0)s, %(conversion_events_1)s)
        AND m.timestamp >= %(window_start)s
        AND m.timestamp < %(window_end)s
    WHERE e.quarantined = 0
    GROUP BY e.identifier, e.variant
)
SELECT
    variant,
    metric_index,
    date_trunc('hour', first_conversion) AS bucket,
    count(*) AS converted_identities
FROM first_conversions
CROSS JOIN LATERAL (SELECT decode(position, 0, 0, 1, 4) AS metric_index, decode(position, 0, c0, 1, c4) AS first_conversion FROM VALUES (0), (1) AS positions(position)) AS zipped
WHERE first_conversion IS NOT NULL
GROUP BY variant, metric_index, bucket
ORDER BY bucket"""
)

CONVERSIONS_DAY_SQL = CONVERSIONS_HOUR_SQL.replace(
    "date_trunc('hour'", "date_trunc('day'"
)


@pytest.mark.parametrize(
    "build_sql, expected_sql",
    [
        (partial(event_names_query, SNOWFLAKE_DIALECT), EVENT_NAMES_SQL),
        (partial(event_stats_query, SNOWFLAKE_DIALECT), EVENT_STATS_SQL),
        (
            partial(exposure_buckets_query, SNOWFLAKE_DIALECT, "hour"),
            EXPOSURE_BUCKETS_HOUR_SQL,
        ),
        (
            partial(exposure_buckets_query, SNOWFLAKE_DIALECT, "day"),
            EXPOSURE_BUCKETS_DAY_SQL,
        ),
        (
            ResultsQueryBuilder([], SNOWFLAKE_DIALECT).build_query,
            RESULTS_NO_METRICS_SQL,
        ),
        (ResultsQueryBuilder(SPECS, SNOWFLAKE_DIALECT).build_query, RESULTS_SQL),
        (
            partial(
                ResultsQueryBuilder(SPECS, SNOWFLAKE_DIALECT).build_conversions_query,
                granularity="hour",
            ),
            CONVERSIONS_HOUR_SQL,
        ),
        (
            partial(
                ResultsQueryBuilder(SPECS, SNOWFLAKE_DIALECT).build_conversions_query,
                granularity="day",
            ),
            CONVERSIONS_DAY_SQL,
        ),
    ],
    ids=[
        "event-names",
        "event-stats",
        "exposure-buckets-hour",
        "exposure-buckets-day",
        "results-no-metrics",
        "results-every-aggregation",
        "conversions-hour",
        "conversions-day",
    ],
)
def test_query_builder__snowflake_dialect__returns_expected_sql(
    build_sql: Callable[[], str | None],
    expected_sql: str,
) -> None:
    # Given / When
    sql = build_sql()

    # Then
    assert sql == expected_sql


def test_results_query_params__snowflake_dialect__binds_each_listed_event() -> None:
    # Given
    builder = ResultsQueryBuilder(SPECS, SNOWFLAKE_DIALECT)

    # When
    params = builder.params(
        environment_key="env-key",
        feature_name="checkout_flow",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
    )

    # Then
    assert params == {
        "environment_key": "env-key",
        "exposure_event": "$flag_exposure",
        "feature_name": "checkout_flow",
        "window_start": WINDOW_START,
        "window_end": WINDOW_END,
        "metric_events_0": "purchase",
        "metric_events_1": "page_view",
        "metric_events_2": "revenue",
        "metric_events_3": "basket_size",
        "metric_events_4": "signup",
        "conversion_events_0": "purchase",
        "conversion_events_1": "signup",
        "metric_0_event": "purchase",
        "metric_1_event": "page_view",
        "metric_2_event": "revenue",
        "metric_3_event": "basket_size",
        "metric_4_event": "signup",
    }
