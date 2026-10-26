from datetime import datetime, timezone
from typing import Any, cast

import pytest
from django.db import connection

from experimentation.dataclasses import (
    ConversionBucket,
    ExposureBucket,
    MetricSpec,
    WarehouseEventNames,
    WarehouseEventStats,
)
from experimentation.models import MetricAggregation
from experimentation.stats import VariantStats
from experimentation.types import ExposureGranularity
from experimentation.warehouses.dialect import POSTGRES_DIALECT
from experimentation.warehouses.queries import (
    QueryResult,
    build_event_names,
    build_event_stats,
    event_names_query,
    event_names_query_params,
    event_stats_query,
    read_exposure_buckets,
    read_results_aggregates,
)

ENV = "env-key"
OTHER_ENV = "other-env"
FEATURE = "checkout_flow"
EXPOSURE = "$flag_exposure"

WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 8, tzinfo=timezone.utc)


def _at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 1, day, hour, minute, tzinfo=timezone.utc)


# (environment_key, identifier, event, feature_name, value, timestamp)
EVENTS: list[tuple[str, str, str, str | None, str | None, datetime]] = [
    # u1: duplicated exposure, counted once from the first.
    (ENV, "u1", EXPOSURE, FEATURE, "control", _at(1, 10, 15)),
    (ENV, "u1", EXPOSURE, FEATURE, "control", _at(1, 10, 20)),
    (ENV, "u2", EXPOSURE, FEATURE, "treatment", _at(1, 12, 5)),
    (ENV, "u3", EXPOSURE, FEATURE, "treatment", _at(2, 8)),
    # u4 and u5 saw two values, so are quarantined; NULL counts as one.
    (ENV, "u4", EXPOSURE, FEATURE, "control", _at(1, 10, 30)),
    (ENV, "u4", EXPOSURE, FEATURE, "treatment", _at(1, 10, 40)),
    (ENV, "u5", EXPOSURE, FEATURE, "control", _at(1, 11)),
    (ENV, "u5", EXPOSURE, FEATURE, None, _at(1, 11, 10)),
    # Not exposures of this feature in this window and environment.
    (ENV, "u6", EXPOSURE, None, "control", _at(1, 10)),
    (
        ENV,
        "u7",
        EXPOSURE,
        FEATURE,
        "control",
        datetime(2025, 12, 31, 23, tzinfo=timezone.utc),
    ),
    (OTHER_ENV, "u8", EXPOSURE, FEATURE, "control", _at(1, 10)),
    (ENV, "u9", EXPOSURE, "other_flag", "control", _at(1, 10)),
    # u1 metrics: one page view lands before exposure; '' and 'true' read as zero.
    (ENV, "u1", "purchase", None, None, _at(1, 11, 30)),
    (ENV, "u1", "page_view", None, None, _at(1, 10)),
    (ENV, "u1", "page_view", None, None, _at(1, 10, 50)),
    (ENV, "u1", "page_view", None, None, _at(1, 11)),
    (ENV, "u1", "revenue", None, "10.5", _at(1, 11, 40)),
    (ENV, "u1", "revenue", None, "", _at(1, 11, 45)),
    (ENV, "u1", "revenue", None, "true", _at(1, 11, 50)),
    (ENV, "u1", "basket_size", None, "3", _at(1, 12)),
    (ENV, "u1", "basket_size", None, "4", _at(1, 12, 10)),
    (OTHER_ENV, "u1", "revenue", None, "1000", _at(1, 11)),
    # u2 metrics: overflow, NULL and junk read as zero; one revenue is past the window.
    (ENV, "u2", "purchase", None, None, _at(2, 9)),
    (ENV, "u2", "purchase", None, None, _at(2, 10)),
    (ENV, "u2", "page_view", None, None, _at(1, 13)),
    (ENV, "u2", "revenue", None, "20", _at(1, 13)),
    (ENV, "u2", "revenue", None, "1e400", _at(1, 13, 5)),
    (ENV, "u2", "revenue", None, None, _at(1, 13, 10)),
    (ENV, "u2", "revenue", None, "500", _at(8, 0)),
    (ENV, "u2", "basket_size", None, "abc", _at(1, 13)),
    (ENV, "u2", "basket_size", None, "5", _at(1, 13, 5)),
    # u3 purchased before exposure, and has no basket events.
    (ENV, "u3", "purchase", None, None, _at(2, 7)),
    (ENV, "u3", "revenue", None, None, _at(2, 9)),
    # Quarantined identities' metrics are excluded.
    (ENV, "u4", "purchase", None, None, _at(1, 11)),
    (ENV, "u4", "revenue", None, "100", _at(1, 11)),
]

SPECS = [
    MetricSpec(11, "purchase", MetricAggregation.OCCURRENCE, False),
    MetricSpec(12, "page_view", MetricAggregation.COUNT, False),
    MetricSpec(13, "revenue", MetricAggregation.SUM, False),
    MetricSpec(14, "basket_size", MetricAggregation.MEAN, False),
    MetricSpec(15, "page_view", MetricAggregation.OCCURRENCE, False),
]


@pytest.fixture()
def events_table(db: None) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE TEMPORARY TABLE events ("
            "environment_key TEXT, event TEXT, feature_name TEXT, "
            "timestamp TIMESTAMPTZ, collected_at TIMESTAMPTZ, identifier TEXT, "
            "value TEXT, traits TEXT, metadata TEXT, "
            "sdk_language TEXT, sdk_version TEXT)"
        )
        cursor.executemany(
            "INSERT INTO events "
            "(environment_key, identifier, event, feature_name, value, timestamp) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            EVENTS,
        )


def _run_query(sql: str, params: dict[str, object]) -> QueryResult:
    with connection.cursor() as cursor:
        cursor.execute(sql, cast(dict[str, Any], params))
        return QueryResult(
            rows=cursor.fetchall(),
            columns=[column.name for column in cursor.description],
        )


def _by_bucket(buckets: list[ExposureBucket]) -> list[ExposureBucket]:
    return sorted(buckets, key=lambda b: (b.bucket, b.variant))


def test_event_names_query__postgres__returns_latest_first(
    events_table: None,
) -> None:
    # Given
    params: dict[str, object] = {**event_names_query_params(ENV)}

    # When
    rows, _columns = _run_query(event_names_query(POSTGRES_DIALECT), params)

    # Then
    assert build_event_names(rows) == WarehouseEventNames(
        events=["revenue", "purchase", EXPOSURE, "basket_size", "page_view"],
        is_truncated=False,
    )


def test_event_stats_query__postgres__counts_environment_events(
    events_table: None,
) -> None:
    # Given
    params: dict[str, object] = {"environment_key": ENV}

    # When
    rows, columns = _run_query(event_stats_query(POSTGRES_DIALECT), params)

    # Then
    assert columns == ["total", "unique"]
    assert build_event_stats(rows) == WarehouseEventStats(
        total_events_received=33,
        unique_events_count=5,
    )


@pytest.mark.parametrize(
    "granularity, expected",
    [
        (
            "hour",
            [
                ExposureBucket("", _at(1, 10), 1, quarantined=True),
                ExposureBucket("control", _at(1, 10), 1),
                ExposureBucket("", _at(1, 11), 1, quarantined=True),
                ExposureBucket("treatment", _at(1, 12), 1),
                ExposureBucket("treatment", _at(2, 8), 1),
            ],
        ),
        (
            "day",
            [
                ExposureBucket("", _at(1, 0), 2, quarantined=True),
                ExposureBucket("control", _at(1, 0), 1),
                ExposureBucket("treatment", _at(1, 0), 1),
                ExposureBucket("treatment", _at(2, 0), 1),
            ],
        ),
    ],
    ids=["hour", "day"],
)
def test_read_exposure_buckets__postgres__buckets_first_exposures(
    events_table: None,
    granularity: ExposureGranularity,
    expected: list[ExposureBucket],
) -> None:
    # Given / When
    buckets = read_exposure_buckets(
        _run_query,
        POSTGRES_DIALECT,
        environment_key=ENV,
        feature_name=FEATURE,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        granularity=granularity,
    )

    # Then
    assert _by_bucket(buckets) == expected
    assert all(b.bucket.tzinfo is not None for b in buckets)


def test_read_results_aggregates__every_aggregation__returns_expected_stats(
    events_table: None,
) -> None:
    # Given / When
    aggregates = read_results_aggregates(
        _run_query,
        POSTGRES_DIALECT,
        environment_key=ENV,
        feature_name=FEATURE,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        specs=SPECS,
        granularity="day",
    )

    # Then
    assert aggregates.exposure_counts == {"control": 1, "treatment": 2}
    assert aggregates.metric_stats == {
        11: {
            "control": VariantStats(n=1, sum=1, sum_squares=1),
            "treatment": VariantStats(n=2, sum=1, sum_squares=1),
        },
        12: {
            "control": VariantStats(n=1, sum=2, sum_squares=4),
            "treatment": VariantStats(n=2, sum=1, sum_squares=1),
        },
        13: {
            "control": VariantStats(n=1, sum=10.5, sum_squares=110.25),
            "treatment": VariantStats(n=2, sum=20, sum_squares=400),
        },
        14: {
            "control": VariantStats(n=1, sum=3.5, sum_squares=12.25),
            "treatment": VariantStats(n=2, sum=2.5, sum_squares=6.25),
        },
        15: {
            "control": VariantStats(n=1, sum=1, sum_squares=1),
            "treatment": VariantStats(n=2, sum=1, sum_squares=1),
        },
    }
    assert {
        metric_id: sorted(buckets, key=lambda b: (b.bucket, b.variant))
        for metric_id, buckets in aggregates.conversion_buckets.items()
    } == {
        11: [
            ConversionBucket("control", _at(1, 0), 1),
            ConversionBucket("treatment", _at(2, 0), 1),
        ],
        15: [
            ConversionBucket("control", _at(1, 0), 1),
            ConversionBucket("treatment", _at(1, 0), 1),
        ],
    }


@pytest.mark.parametrize(
    "value, expected",
    [
        ("-2", -2.0),
        ("1E-2", 0.01),
        (".5", 0.5),
        ("7.", 7.0),
        ("9" * 30 + "." + "9" * 30 + "e99", 1e129),
        ("1" * 31, 0.0),
        ("inf", 0.0),
        ("nan", 0.0),
        ("1e400", 0.0),
        (None, 0.0),
        ("true", 0.0),
        (" 1", 0.0),
        ("\u0661", 0.0),
    ],
    ids=[
        "signed",
        "exponent",
        "leading-point",
        "trailing-point",
        "30-digit-bound",
        "31-digits",
        "inf",
        "nan",
        "overflow",
        "null",
        "junk",
        "leading-space",
        "non-ascii-digit",
    ],
)
def test_postgres_float_or_zero__value__casts_numbers_and_zeroes_the_rest(
    db: None,
    value: str | None,
    expected: float,
) -> None:
    # Given
    expr = f"{POSTGRES_DIALECT.param('value')}::text"

    # When
    rows, _columns = _run_query(
        f"SELECT {POSTGRES_DIALECT.float_or_zero(expr)}", {"value": value}
    )

    # Then
    assert rows[0][0] == pytest.approx(expected)
