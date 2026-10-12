from collections.abc import Callable

import pytest

from experimentation.warehouses.dialect import POSTGRES_DIALECT, PostgresDialect

NUMERIC_PATTERN = r"^[-+]?(\d{1,30}(\.\d{0,30})?|\.\d{1,30})([eE][-+]?\d{1,2})?$"


@pytest.mark.parametrize(
    "render, expected",
    [
        (lambda d: d.param("limit"), "%(limit)s"),
        (
            lambda d: d.in_list("m.event", "metric_events", 3),
            "m.event = ANY(%(metric_events)s)",
        ),
        (lambda d: d.count_all(), "count(*)"),
        (lambda d: d.count_if("x > 1"), "count(*) FILTER (WHERE x > 1)"),
        (lambda d: d.count_distinct("event"), "count(DISTINCT event)"),
        (lambda d: d.any_value("value"), "min(value)"),
        (
            lambda d: d.time_bucket("ts", "hour"),
            "date_trunc('hour', ts AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'",
        ),
        (
            lambda d: d.time_bucket("ts", "day"),
            "date_trunc('day', ts AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'",
        ),
        (
            lambda d: d.float_or_zero("m.value"),
            f"CASE WHEN m.value ~ '{NUMERIC_PATTERN}' "
            "THEN (m.value)::double precision ELSE 0 END",
        ),
        (lambda d: d.sum_if("v", "c"), "coalesce(sum(v) FILTER (WHERE c), 0)"),
        (lambda d: d.avg_if("v", "c"), "coalesce(avg(v) FILTER (WHERE c), 0)"),
        (lambda d: d.min_if("v", "c"), "min(v) FILTER (WHERE c)"),
        (lambda d: d.bool_to_number("x > 0"), "(x > 0)::int"),
        (
            lambda d: d.zip_unnest({"a": ["0", "4"], "b": ["c0", "c4"]}),
            "CROSS JOIN LATERAL unnest(ARRAY[0, 4], ARRAY[c0, c4]) AS zipped(a, b)",
        ),
    ],
    ids=[
        "param",
        "in_list",
        "count_all",
        "count_if",
        "count_distinct",
        "any_value",
        "time_bucket-hour",
        "time_bucket-day",
        "float_or_zero",
        "sum_if",
        "avg_if",
        "min_if",
        "bool_to_number",
        "zip_unnest",
    ],
)
def test_postgres_dialect__fragment__renders_expected_sql(
    render: Callable[[PostgresDialect], str],
    expected: str,
) -> None:
    # Given
    dialect = POSTGRES_DIALECT

    # When
    sql = render(dialect)

    # Then
    assert sql == expected


def test_postgres_dialect_list_params__values__binds_one_array() -> None:
    # Given
    values = ("purchase", "signup")

    # When
    params = POSTGRES_DIALECT.list_params("metric_events", values)

    # Then
    assert params == {"metric_events": ["purchase", "signup"]}
