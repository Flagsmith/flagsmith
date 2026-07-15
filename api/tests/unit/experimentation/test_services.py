from dataclasses import asdict
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from django.db.models import Q
from flag_engine.segments.constants import PERCENTAGE_SPLIT
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from rest_framework.exceptions import ValidationError

from core.dataclasses import AuthorData
from environments.models import Environment
from experimentation import services
from experimentation.dataclasses import (
    ExposureBucket,
    ExposuresSummary,
    ExposuresTimeseries,
    ExposuresTimeseriesPoint,
    MetricSpec,
    ResultsAggregates,
    RolloutSpec,
    WarehouseEventStats,
)
from experimentation.models import (
    ExpectedDirection,
    Experiment,
    ExperimentMetric,
    ExperimentStatus,
    Metric,
    MetricAggregation,
    MetricDirection,
    WarehouseConnection,
    WarehouseConnectionStatus,
    WarehouseType,
)
from experimentation.results_query import _MetricSlot
from experimentation.stats import VariantStats
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import STRING
from features.versioning.dataclasses import MultivariateValueChangeSet
from segments.models import Condition
from users.models import FFAdminUser
from util.mappers import map_environment_to_environment_document


def test_get_clickhouse_client__configured_url__builds_client_with_timeouts(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.EXPERIMENTATION_CLICKHOUSE_URL = (
        "clickhouse://user:pass@ch.example.com:9440/flagsmith_exp?secure=True"
    )
    mock_client_cls = mocker.patch("experimentation.services.Client")
    services._get_clickhouse_client.cache_clear()

    # When
    client = services._get_clickhouse_client()

    # Then
    mock_client_cls.assert_called_once_with(
        "ch.example.com",
        port=9440,
        database="flagsmith_exp",
        user="user",
        password="pass",
        secure=True,
        connect_timeout=services.CLICKHOUSE_CONNECT_TIMEOUT_SECONDS,
        send_receive_timeout=services.CLICKHOUSE_QUERY_TIMEOUT_SECONDS,
    )
    assert client is mock_client_cls.return_value
    services._get_clickhouse_client.cache_clear()


def test_get_clickhouse_client__dsn_timeouts__are_preserved(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.EXPERIMENTATION_CLICKHOUSE_URL = (
        "clickhouse://ch.example.com:9000/db?connect_timeout=1&send_receive_timeout=2"
    )
    mock_client_cls = mocker.patch("experimentation.services.Client")
    services._get_clickhouse_client.cache_clear()

    # When
    services._get_clickhouse_client()

    # Then
    mock_client_cls.assert_called_once_with(
        "ch.example.com",
        port=9000,
        database="db",
        connect_timeout=1,
        send_receive_timeout=2,
    )
    services._get_clickhouse_client.cache_clear()


def test_get_unique_event_names__events_present__returns_ordered_names(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mock_client.execute.return_value = [("conversion",), ("page_view",)]
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )

    # When
    result = services.get_unique_event_names("env-key-123")

    # Then
    assert result == ["conversion", "page_view"]
    mock_client.execute.assert_called_once_with(
        "SELECT DISTINCT event FROM events "
        "WHERE environment_key = %(environment_key)s "
        "ORDER BY event",
        {"environment_key": "env-key-123"},
    )


def test_get_exposure_buckets__day_granularity__queries_and_maps_rows(
    mocker: MockerFixture,
) -> None:
    # Given the warehouse returns one bucket row per variant per day, plus a
    # quarantined row (aware datetimes: the bucket column type carries 'UTC')
    rows = [
        (0, "control", datetime(2026, 6, 1, tzinfo=timezone.utc), 100),
        (0, "variant_a", datetime(2026, 6, 1, tzinfo=timezone.utc), 90),
        (1, "", datetime(2026, 6, 1, tzinfo=timezone.utc), 5),
    ]
    mock_client = mocker.Mock()
    mock_client.execute.return_value = rows
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )
    window_start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    window_end = datetime(2026, 6, 10, tzinfo=timezone.utc)

    # When
    result = services.get_exposure_buckets(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=window_start,
        window_end=window_end,
        granularity="day",
    )

    # Then the rows are mapped to dataclasses
    assert result == [
        ExposureBucket(
            variant="control",
            bucket=datetime(2026, 6, 1, tzinfo=timezone.utc),
            first_exposed_identities=100,
        ),
        ExposureBucket(
            variant="variant_a",
            bucket=datetime(2026, 6, 1, tzinfo=timezone.utc),
            first_exposed_identities=90,
        ),
        ExposureBucket(
            variant="",
            bucket=datetime(2026, 6, 1, tzinfo=timezone.utc),
            first_exposed_identities=5,
            quarantined=True,
        ),
    ]
    # And the query buckets first exposures by UTC day over a half-open
    # window, deduplicates identities, and flags identities seen in more
    # than one variant
    sql, params = mock_client.execute.call_args.args
    assert "toStartOfDay(first_exposure, 'UTC') AS bucket" in sql
    assert "GROUP BY identifier" in sql
    assert "uniqExact(value) > 1 AS quarantined" in sql
    assert "timestamp >= %(window_start)s" in sql
    assert "timestamp < %(window_end)s" in sql
    assert params == {
        "environment_key": "env-key-123",
        "exposure_event": "$flag_exposure",
        "feature_name": "my-feature",
        "window_start": window_start,
        "window_end": window_end,
    }


def test_get_exposure_buckets__hour_granularity__buckets_by_hour(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mock_client.execute.return_value = []
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )

    # When
    result = services.get_exposure_buckets(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 2, tzinfo=timezone.utc),
        granularity="hour",
    )

    # Then
    assert result == []
    sql, _ = mock_client.execute.call_args.args
    assert "toStartOfHour(first_exposure, 'UTC') AS bucket" in sql


def test_compute_exposures_payload__window_within_72_hours__hourly_buckets(
    mocker: MockerFixture,
) -> None:
    # Given a window of exactly 72 hours and one exposure row
    mock_client = mocker.Mock()
    mock_client.execute.return_value = [
        (0, "control", datetime(2026, 6, 1, tzinfo=timezone.utc), 10)
    ]
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )

    # When
    summary = services.compute_exposures_summary(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 4, tzinfo=timezone.utc),
    )

    # Then the query and the summary agree on hourly granularity
    sql, _ = mock_client.execute.call_args.args
    assert "toStartOfHour(first_exposure, 'UTC') AS bucket" in sql
    assert summary.timeseries.granularity == "hour"
    assert summary.timeseries.points == [
        ExposuresTimeseriesPoint(
            bucket="2026-06-01T00:00:00+00:00",
            new_identities={"control": 10},
        )
    ]


def test_compute_exposures_payload__window_beyond_72_hours__daily_buckets(
    mocker: MockerFixture,
) -> None:
    # Given a window one second past 72 hours
    mock_client = mocker.Mock()
    mock_client.execute.return_value = []
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )

    # When
    summary = services.compute_exposures_summary(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 4, 0, 0, 1, tzinfo=timezone.utc),
    )

    # Then the query and the summary agree on daily granularity
    sql, _ = mock_client.execute.call_args.args
    assert "toStartOfDay(first_exposure, 'UTC') AS bucket" in sql
    assert summary.timeseries.granularity == "day"
    assert summary.timeseries.points == []


def _bucket(
    variant: str,
    bucket: datetime,
    first_exposed_identities: int,
    quarantined: bool = False,
) -> ExposureBucket:
    return ExposureBucket(
        variant=variant,
        bucket=bucket,
        first_exposed_identities=first_exposed_identities,
        quarantined=quarantined,
    )


def test_build_exposures_summary__multiple_variants__points_grouped_by_bucket() -> None:
    # Given two variants gaining identities over two daily buckets
    day_1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
    day_2 = datetime(2026, 6, 2, tzinfo=timezone.utc)
    buckets = [
        _bucket("control", day_1, 100),
        _bucket("variant_a", day_1, 90),
        _bucket("control", day_2, 50),
        _bucket("variant_a", day_2, 70),
    ]

    # When
    summary = services.build_exposures_summary(buckets, granularity="day")

    # Then
    assert summary == ExposuresSummary(
        excluded_identities=0,
        timeseries=ExposuresTimeseries(
            granularity="day",
            points=[
                ExposuresTimeseriesPoint(
                    bucket="2026-06-01T00:00:00+00:00",
                    new_identities={"control": 100, "variant_a": 90},
                ),
                ExposuresTimeseriesPoint(
                    bucket="2026-06-02T00:00:00+00:00",
                    new_identities={"control": 50, "variant_a": 70},
                ),
            ],
        ),
    )


def test_build_exposures_summary__quarantined_identities__excluded_and_counted() -> (
    None
):
    # Given identities flagged as exposed to more than one variant
    day = datetime(2026, 6, 1, tzinfo=timezone.utc)
    buckets = [
        _bucket("control", day, 100),
        _bucket("variant_a", day, 95),
        _bucket("", day, 5, quarantined=True),
    ]

    # When
    summary = services.build_exposures_summary(buckets, granularity="day")

    # Then they are counted once, out of band, and kept out of the timeseries
    assert summary.excluded_identities == 5
    assert summary.timeseries.points == [
        ExposuresTimeseriesPoint(
            bucket="2026-06-01T00:00:00+00:00",
            new_identities={"control": 100, "variant_a": 95},
        )
    ]


def test_build_exposures_summary__unordered_sparse_buckets__points_sorted_and_sparse() -> (  # noqa: E501
    None
):
    # Given out-of-order buckets for variants arriving on different days
    day_1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
    day_2 = datetime(2026, 6, 2, tzinfo=timezone.utc)
    buckets = [
        _bucket("variant_a", day_2, 7),
        _bucket("control", day_1, 10),
    ]

    # When
    summary = services.build_exposures_summary(buckets, granularity="day")

    # Then points are chronological and only carry the variants seen in them
    assert summary.timeseries == ExposuresTimeseries(
        granularity="day",
        points=[
            ExposuresTimeseriesPoint(
                bucket="2026-06-01T00:00:00+00:00",
                new_identities={"control": 10},
            ),
            ExposuresTimeseriesPoint(
                bucket="2026-06-02T00:00:00+00:00",
                new_identities={"variant_a": 7},
            ),
        ],
    )


def test_build_exposures_summary__no_buckets__empty_summary() -> None:
    # Given no exposure data
    # When
    summary = services.build_exposures_summary([], granularity="hour")

    # Then the summary is empty but fully shaped
    assert summary == ExposuresSummary(
        excluded_identities=0,
        timeseries=ExposuresTimeseries(granularity="hour", points=[]),
    )


def test_get_unique_event_names__no_events__returns_empty_list(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mock_client.execute.return_value = []
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )

    # When
    result = services.get_unique_event_names("env-key-123")

    # Then
    assert result == []


@pytest.mark.parametrize(
    "rows, expected_total, expected_unique",
    [
        ([(42, 3)], 42, 3),
        ([], 0, 0),
    ],
    ids=["events_present", "empty_result_set"],
)
def test_get_warehouse_event_stats__rows__returns_counts(
    mocker: MockerFixture,
    rows: list[tuple[int, int]],
    expected_total: int,
    expected_unique: int,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mock_client.execute.return_value = rows
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )

    # When
    result = services.get_warehouse_event_stats("env-key-123")

    # Then
    assert result.total_events_received == expected_total
    assert result.unique_events_count == expected_unique
    mock_client.execute.assert_called_once_with(
        "SELECT count() AS total, uniqExact(event) AS unique "
        "FROM events WHERE environment_key = %(environment_key)s",
        {"environment_key": "env-key-123"},
    )


@pytest.mark.django_db
def test_mark_warehouse_pending_connection__created__transitions_to_pending(
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given
    connection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
    )

    # When
    result = services.mark_warehouse_pending_connection(connection)

    # Then
    assert result.status == WarehouseConnectionStatus.PENDING_CONNECTION
    connection.refresh_from_db()
    assert connection.status == WarehouseConnectionStatus.PENDING_CONNECTION
    assert log.events == [
        {
            "level": "info",
            "event": "connection.test_event_sent",
            "environment__id": environment.id,
            "organisation__id": environment.project.organisation_id,
        }
    ]


@pytest.mark.django_db
def test_mark_warehouse_pending_connection__already_pending__is_noop(
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given
    connection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
        status=WarehouseConnectionStatus.PENDING_CONNECTION,
    )

    # When
    result = services.mark_warehouse_pending_connection(connection)

    # Then
    assert result.status == WarehouseConnectionStatus.PENDING_CONNECTION
    assert log.events == []


@pytest.mark.django_db
def test_refresh_warehouse_connection_status__events_exist__transitions_to_connected(
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given
    connection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
        status=WarehouseConnectionStatus.PENDING_CONNECTION,
    )
    stats = WarehouseEventStats(total_events_received=5, unique_events_count=1)

    # When
    result = services.refresh_warehouse_connection_status(connection, stats)

    # Then
    assert result.status == WarehouseConnectionStatus.CONNECTED
    connection.refresh_from_db()
    assert connection.status == WarehouseConnectionStatus.CONNECTED
    assert log.events == [
        {
            "level": "info",
            "event": "connection.connected",
            "environment__id": environment.id,
            "organisation__id": environment.project.organisation_id,
        }
    ]


@pytest.mark.django_db
def test_refresh_warehouse_connection_status__no_events__stays_pending(
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given
    connection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
        status=WarehouseConnectionStatus.PENDING_CONNECTION,
    )
    stats = WarehouseEventStats(total_events_received=0, unique_events_count=0)

    # When
    result = services.refresh_warehouse_connection_status(connection, stats)

    # Then
    assert result.status == WarehouseConnectionStatus.PENDING_CONNECTION
    assert log.events == []


@pytest.mark.django_db
def test_refresh_warehouse_connection_status__already_connected__is_noop(
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given
    connection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
        status=WarehouseConnectionStatus.CONNECTED,
    )
    stats = WarehouseEventStats(total_events_received=99, unique_events_count=4)

    # When
    result = services.refresh_warehouse_connection_status(connection, stats)

    # Then
    assert result.status == WarehouseConnectionStatus.CONNECTED
    assert log.events == []


def _spec(
    metric_id: int = 7,
    event: str = "purchase",
    aggregation: str = MetricAggregation.OCCURRENCE,
    lower_is_better: bool = False,
) -> MetricSpec:
    return MetricSpec(
        metric_id=metric_id,
        event=event,
        aggregation=aggregation,
        lower_is_better=lower_is_better,
    )


def _aggregates(
    specs: list[MetricSpec],
    exposure_counts: dict[str, int],
    metric_stats: dict[int, dict[str, VariantStats]],
) -> ResultsAggregates:
    return ResultsAggregates(
        specs=specs,
        exposure_counts=exposure_counts,
        metric_stats=metric_stats,
    )


def _result_columns(metric_count: int) -> list[tuple[str, str]]:
    """The `(name, type)` metadata clickhouse-driver returns for the results
    query with `with_column_types=True`, in SELECT order."""
    columns = [("variant", "String"), ("n", "UInt64")]
    for i in range(metric_count):
        columns.append((f"m{i}_sum", "Float64"))
        columns.append((f"m{i}_sum_squares", "Float64"))
    return columns


def test_get_metric_variant_stats__metrics__queries_and_maps_rows(
    mocker: MockerFixture,
) -> None:
    # Given the warehouse returns per-variant counts for all four aggregation types
    rows = [
        ("control", 1000, 100.0, 100.0, 5000.0, 30000.0, 3000.0, 9000.0, 200.0, 500.0),
        (
            "variant_a",
            1000,
            120.0,
            120.0,
            5200.0,
            31000.0,
            3200.0,
            9500.0,
            210.0,
            520.0,
        ),
    ]
    mock_client = mocker.Mock()
    mock_client.execute.return_value = (rows, _result_columns(4))
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )
    specs = [
        _spec(metric_id=7, event="purchase", aggregation=MetricAggregation.OCCURRENCE),
        _spec(metric_id=9, event="revenue", aggregation=MetricAggregation.SUM),
        _spec(metric_id=11, event="page_view", aggregation=MetricAggregation.COUNT),
        _spec(metric_id=13, event="session", aggregation=MetricAggregation.MEAN),
    ]
    window_start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    window_end = datetime(2026, 6, 10, tzinfo=timezone.utc)

    # When
    aggregates = services.get_metric_variant_stats(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=window_start,
        window_end=window_end,
        specs=specs,
    )

    # Then per-variant counts and sufficient statistics are mapped per metric
    assert aggregates.exposure_counts == {"control": 1000, "variant_a": 1000}
    assert aggregates.metric_stats[7]["variant_a"] == VariantStats(
        n=1000, sum=120.0, sum_squares=120.0
    )
    assert aggregates.metric_stats[9]["control"] == VariantStats(
        n=1000, sum=5000.0, sum_squares=30000.0
    )
    assert aggregates.metric_stats[11]["control"] == VariantStats(
        n=1000, sum=3000.0, sum_squares=9000.0
    )
    assert aggregates.metric_stats[13]["variant_a"] == VariantStats(
        n=1000, sum=210.0, sum_squares=520.0
    )
    # And the query joins post-exposure metric events and excludes quarantined
    sql, params = mock_client.execute.call_args.args
    assert "LEFT JOIN events AS m" in sql
    assert "m.timestamp >= e.first_exposure" in sql
    assert "m.timestamp >= %(window_start)s" in sql
    assert "timestamp < %(window_end)s" in sql
    assert "WHERE e.quarantined = 0" in sql
    assert (
        "countIf(m.event = %(metric_0_event)s AND m.timestamp >= e.first_exposure)"
        " > 0 AS m0" in sql
    )
    assert (
        "sumIf(toFloat64OrZero(m.value), m.event = %(metric_1_event)s"
        " AND m.timestamp >= e.first_exposure) AS m1" in sql
    )
    assert (
        "countIf(m.event = %(metric_2_event)s AND m.timestamp >= e.first_exposure)"
        " AS m2" in sql
    )
    assert (
        "if(countIf(m.event = %(metric_3_event)s AND m.timestamp >= e.first_exposure)"
        " > 0, avgIf(toFloat64OrZero(m.value), m.event = %(metric_3_event)s"
        " AND m.timestamp >= e.first_exposure), 0) AS m3" in sql
    )
    assert "sum(m0) AS m0_sum, sum(m0 * m0) AS m0_sum_squares" in sql
    assert params["metric_events"] == ["purchase", "revenue", "page_view", "session"]
    assert params["metric_0_event"] == "purchase"
    assert params["metric_1_event"] == "revenue"
    assert params["metric_2_event"] == "page_view"
    assert params["metric_3_event"] == "session"
    assert params["window_end"] == window_end


def test_get_metric_variant_stats__three_variants__maps_all_variants(
    mocker: MockerFixture,
) -> None:
    # Given three variants returned from the warehouse
    rows = [
        ("control", 1000, 100.0, 100.0, 5000.0, 30000.0),
        ("variant_a", 900, 80.0, 80.0, 4500.0, 25000.0),
        ("variant_b", 950, 110.0, 110.0, 5100.0, 29000.0),
    ]
    mock_client = mocker.Mock()
    mock_client.execute.return_value = (rows, _result_columns(2))
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )
    specs = [
        _spec(metric_id=7, event="purchase", aggregation=MetricAggregation.OCCURRENCE),
        _spec(metric_id=9, event="revenue", aggregation=MetricAggregation.SUM),
    ]

    # When
    aggregates = services.get_metric_variant_stats(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 10, tzinfo=timezone.utc),
        specs=specs,
    )

    # Then all three variants are decoded into counts and metric stats
    assert aggregates.exposure_counts == {
        "control": 1000,
        "variant_a": 900,
        "variant_b": 950,
    }
    assert aggregates.metric_stats[7].keys() == {"control", "variant_a", "variant_b"}
    assert aggregates.metric_stats[9]["variant_b"] == VariantStats(
        n=950, sum=5100.0, sum_squares=29000.0
    )


def test_get_metric_variant_stats__no_metrics__counts_variants_only(
    mocker: MockerFixture,
) -> None:
    # Given an experiment with no attached metrics
    mock_client = mocker.Mock()
    mock_client.execute.return_value = (
        [("control", 1000), ("variant_a", 900)],
        _result_columns(0),
    )
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )

    # When
    aggregates = services.get_metric_variant_stats(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 10, tzinfo=timezone.utc),
        specs=[],
    )

    # Then only the per-variant counts are returned, with no metric join
    assert aggregates.exposure_counts == {"control": 1000, "variant_a": 900}
    assert aggregates.metric_stats == {}
    sql, params = mock_client.execute.call_args.args
    assert "SELECT variant, count() AS n" in sql
    assert "LEFT JOIN" not in sql
    assert "metric_events" not in params


def test_get_metric_variant_stats__shuffled_columns__maps_by_name(
    mocker: MockerFixture,
) -> None:
    # Given column metadata in a different order than the natural SELECT, with
    # each row's values laid out to match that shuffled order
    columns = [
        ("m1_sum_squares", "Float64"),
        ("variant", "String"),
        ("m0_sum", "Float64"),
        ("n", "UInt64"),
        ("m1_sum", "Float64"),
        ("m0_sum_squares", "Float64"),
    ]
    rows = [(30000.0, "control", 100.0, 1000, 5000.0, 100.0)]
    mock_client = mocker.Mock()
    mock_client.execute.return_value = (rows, columns)
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )
    specs = [
        _spec(metric_id=7, event="purchase", aggregation=MetricAggregation.OCCURRENCE),
        _spec(metric_id=9, event="revenue", aggregation=MetricAggregation.SUM),
    ]

    # When
    aggregates = services.get_metric_variant_stats(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 10, tzinfo=timezone.utc),
        specs=specs,
    )

    # Then values are decoded by column name, not position
    assert aggregates.exposure_counts == {"control": 1000}
    assert aggregates.metric_stats[7]["control"] == VariantStats(
        n=1000, sum=100.0, sum_squares=100.0
    )
    assert aggregates.metric_stats[9]["control"] == VariantStats(
        n=1000, sum=5000.0, sum_squares=30000.0
    )


@pytest.mark.parametrize(
    "aggregation, expected",
    [
        (
            MetricAggregation.OCCURRENCE,
            "countIf(m.event = %(metric_0_event)s AND m.timestamp >= e.first_exposure) > 0 AS m0",
        ),
        (
            MetricAggregation.COUNT,
            "countIf(m.event = %(metric_0_event)s AND m.timestamp >= e.first_exposure) AS m0",
        ),
        (
            MetricAggregation.SUM,
            "sumIf(toFloat64OrZero(m.value), m.event = %(metric_0_event)s AND m.timestamp >= e.first_exposure) AS m0",
        ),
        (
            MetricAggregation.MEAN,
            "if(countIf(m.event = %(metric_0_event)s AND m.timestamp >= e.first_exposure) > 0, "
            "avgIf(toFloat64OrZero(m.value), m.event = %(metric_0_event)s AND m.timestamp >= e.first_exposure), 0) AS m0",
        ),
    ],
    ids=["occurrence", "count", "sum", "mean"],
)
def test_metric_slot_unit_select__aggregation__builds_expression(
    aggregation: str,
    expected: str,
) -> None:
    # Given a metric slot for each aggregation type
    # When / Then it produces the correct per-identity unit-value expression
    assert (
        _MetricSlot(spec=_spec(aggregation=aggregation), index=0).unit_select()
        == expected
    )


def test_metric_slot_unit_select__unknown_aggregation__raises() -> None:
    # Given an aggregation the slot does not support
    # When / Then it refuses rather than silently emitting the wrong clause
    with pytest.raises(ValueError, match="Unsupported metric aggregation"):
        _MetricSlot(spec=_spec(aggregation="median"), index=0).unit_select()


def test_build_results_summary__healthy_arms__infers_each_treatment() -> None:
    # Given a 10% control and a 12% treatment, both well above the floor
    control = VariantStats(n=1000, sum=100.0, sum_squares=100.0)
    treatment = VariantStats(n=1000, sum=120.0, sum_squares=120.0)
    aggregates = _aggregates(
        [_spec(metric_id=7)],
        {"control": 1000, "variant_a": 1000},
        {7: {"control": control, "variant_a": treatment}},
    )

    # When
    summary = services.build_results_summary(
        aggregates,
        expected_shares={"control": 0.5, "variant_a": 0.5},
    )

    # Then the treatment is compared to control and the raw stats are kept
    assert summary.metrics[0].variants == {
        "control": control,
        "variant_a": treatment,
    }
    inference = summary.metrics[0].inference["variant_a"]
    assert inference is not None
    assert inference.lift == pytest.approx(0.2)
    assert inference.chance_to_win == pytest.approx(0.90379, abs=1e-4)


def test_build_results_summary__below_identity_floor__inference_none() -> None:
    # Given arms below the minimum identities per variant
    arm = VariantStats(n=40, sum=4.0, sum_squares=4.0)
    aggregates = _aggregates(
        [_spec(metric_id=7)],
        {"control": 40, "variant_a": 40},
        {7: {"control": arm, "variant_a": arm}},
    )

    # When
    summary = services.build_results_summary(aggregates, expected_shares={})

    # Then inference is withheld
    assert summary.metrics[0].inference["variant_a"] is None


def test_build_results_summary__occurrence_below_conversion_floor__inference_none() -> (
    None
):
    # Given enough identities but too few conversions on an occurrence metric
    control = VariantStats(n=100, sum=10.0, sum_squares=10.0)
    treatment = VariantStats(n=100, sum=3.0, sum_squares=3.0)
    aggregates = _aggregates(
        [_spec(metric_id=7, aggregation=MetricAggregation.OCCURRENCE)],
        {"control": 100, "variant_a": 100},
        {7: {"control": control, "variant_a": treatment}},
    )

    # When
    summary = services.build_results_summary(aggregates, expected_shares={})

    # Then inference is withheld
    assert summary.metrics[0].inference["variant_a"] is None


def test_build_results_summary__lower_is_better__flips_chance_to_win() -> None:
    # Given a value metric where a fall is the win
    control = VariantStats(n=1000, sum=100.0, sum_squares=100.0)
    treatment = VariantStats(n=1000, sum=120.0, sum_squares=120.0)
    aggregates = _aggregates(
        [_spec(metric_id=7, aggregation=MetricAggregation.SUM, lower_is_better=True)],
        {"control": 1000, "variant_a": 1000},
        {7: {"control": control, "variant_a": treatment}},
    )

    # When
    summary = services.build_results_summary(aggregates, expected_shares={})

    # Then the rise counts against the treatment
    inference = summary.metrics[0].inference["variant_a"]
    assert inference is not None
    assert inference.lift == pytest.approx(0.2)
    assert inference.chance_to_win == pytest.approx(1 - 0.90379, abs=1e-4)


def test_build_results_summary__zero_control_mean__inference_none() -> None:
    # Given a control with no value: the relative lift is undefined
    control = VariantStats(n=100, sum=0.0, sum_squares=0.0)
    treatment = VariantStats(n=100, sum=50.0, sum_squares=50.0)
    aggregates = _aggregates(
        [_spec(metric_id=7, aggregation=MetricAggregation.COUNT)],
        {"control": 100, "variant_a": 100},
        {7: {"control": control, "variant_a": treatment}},
    )

    # When
    summary = services.build_results_summary(aggregates, expected_shares={})

    # Then inference is withheld by the kernel's own guard
    assert summary.metrics[0].inference["variant_a"] is None


def test_build_results_summary__no_control_variant__inference_none() -> None:
    # Given a metric with stats for a treatment but no control
    treatment = VariantStats(n=1000, sum=120.0, sum_squares=120.0)
    aggregates = _aggregates(
        [_spec(metric_id=7)],
        {"variant_a": 1000},
        {7: {"variant_a": treatment}},
    )

    # When
    summary = services.build_results_summary(aggregates, expected_shares={})

    # Then inference is withheld
    assert summary.metrics[0].inference["variant_a"] is None


def test_build_results_summary__balanced_traffic__srm_reports_no_mismatch() -> None:
    # Given a balanced split above the SRM gate
    aggregates = _aggregates([], {"control": 5000, "variant_a": 5000}, {})

    # When
    summary = services.build_results_summary(
        aggregates,
        expected_shares={"control": 0.5, "variant_a": 0.5},
    )

    # Then
    assert summary.srm_p_value == pytest.approx(1.0)
    assert summary.metrics == []


def test_build_results_summary__imbalanced_traffic__srm_below_threshold() -> None:
    # Given a 60/40 split against an expected 50/50
    aggregates = _aggregates([], {"control": 6000, "variant_a": 4000}, {})

    # When
    summary = services.build_results_summary(
        aggregates,
        expected_shares={"control": 0.5, "variant_a": 0.5},
    )

    # Then the mismatch is flagged
    assert summary.srm_p_value is not None
    assert summary.srm_p_value < 0.001


@pytest.mark.parametrize(
    "exposure_counts, expected_shares",
    [
        ({"control": 40, "variant_a": 40}, {"control": 0.5, "variant_a": 0.5}),
        ({"control": 5000, "variant_a": 5000}, {}),
    ],
    ids=["below_gate", "no_expected_shares"],
)
def test_build_results_summary__srm_not_computable__srm_none(
    exposure_counts: dict[str, int],
    expected_shares: dict[str, float],
) -> None:
    # Given too little traffic, or no configured split to compare against
    aggregates = _aggregates([], exposure_counts, {})

    # When
    summary = services.build_results_summary(
        aggregates, expected_shares=expected_shares
    )

    # Then SRM is not reported
    assert summary.srm_p_value is None


def test_build_results_summary__computed__serialises_to_wire_shape() -> None:
    # Given a computed summary
    control = VariantStats(n=1000, sum=100.0, sum_squares=100.0)
    treatment = VariantStats(n=1000, sum=120.0, sum_squares=120.0)
    aggregates = _aggregates(
        [_spec(metric_id=7)],
        {"control": 1000, "variant_a": 1000},
        {7: {"control": control, "variant_a": treatment}},
    )
    summary = services.build_results_summary(
        aggregates,
        expected_shares={"control": 0.5, "variant_a": 0.5},
    )

    # When
    payload = asdict(summary)

    # Then the payload nests raw stats and per-treatment inference
    assert payload["srm_p_value"] == pytest.approx(1.0)
    assert payload["metrics"][0]["metric_id"] == 7
    assert payload["metrics"][0]["variants"]["control"] == {
        "n": 1000,
        "sum": 100.0,
        "sum_squares": 100.0,
    }
    assert set(payload["metrics"][0]["inference"]["variant_a"]) == {
        "lift",
        "ci_low",
        "ci_high",
        "chance_to_win",
    }


@pytest.mark.django_db
def test_experiment_metric_specs__attached_metrics__maps_definition_and_direction(
    experiment: Experiment,
    environment: Environment,
) -> None:
    # Given two metrics attached to the experiment, one lower-is-better
    higher = Metric.objects.create(
        environment=environment,
        name="Revenue",
        aggregation=MetricAggregation.SUM,
        direction=MetricDirection.UP,
        definition={"version": 1, "event": "purchase"},
    )
    lower = Metric.objects.create(
        environment=environment,
        name="Errors",
        aggregation=MetricAggregation.COUNT,
        direction=MetricDirection.DOWN,
        definition={"version": 1, "event": "error"},
    )
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=higher,
        expected_direction=ExpectedDirection.INCREASE,
    )
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=lower,
        expected_direction=ExpectedDirection.DECREASE,
    )

    # When
    specs = services._experiment_metric_specs(experiment)

    # Then each metric maps to its event, aggregation and polarity
    assert specs == [
        MetricSpec(
            metric_id=higher.id,
            event="purchase",
            aggregation=MetricAggregation.SUM,
            lower_is_better=False,
        ),
        MetricSpec(
            metric_id=lower.id,
            event="error",
            aggregation=MetricAggregation.COUNT,
            lower_is_better=True,
        ),
    ]


def _multivariate_feature(
    environment: Environment,
    allocations: dict[str | None, int],
) -> Feature:
    feature: Feature = Feature.objects.create(
        name="results-feature",
        project=environment.project,
        type=MULTIVARIATE,
        initial_value="control",
    )
    for key, allocation in allocations.items():
        MultivariateFeatureOption.objects.create(
            feature=feature,
            key=key,
            default_percentage_allocation=allocation,
            type=STRING,
            string_value=key or "unkeyed",
        )
    return feature


@pytest.mark.django_db
def test_expected_variant_shares__keyed_options__control_takes_remainder(
    environment: Environment,
) -> None:
    # Given a multivariate feature whose options are allocated 30% and 20%
    feature = _multivariate_feature(environment, {"variant_a": 30, "variant_b": 20})
    experiment = Experiment.objects.create(
        environment=environment,
        feature=feature,
        name="exp",
        hypothesis="h",
        status=ExperimentStatus.RUNNING,
    )

    # When
    shares = services._expected_variant_shares(experiment)

    # Then control takes the unallocated remainder
    assert shares == pytest.approx({"variant_a": 0.3, "variant_b": 0.2, "control": 0.5})


@pytest.mark.django_db
def test_expected_variant_shares__null_option_keys__returns_empty(
    experiment: Experiment,
) -> None:
    # Given the experiment's multivariate options carry no variant keys

    # When / Then the split can't be described, so SRM is skipped
    assert services._expected_variant_shares(experiment) == {}


@pytest.mark.django_db
def test_expected_variant_shares__mixed_keyed_and_null_options__returns_empty(
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given a multivariate feature with one keyed and one unkeyed option
    feature = _multivariate_feature(environment, {"variant_a": 30, None: 30})
    experiment = Experiment.objects.create(
        environment=environment,
        feature=feature,
        name="exp",
        hypothesis="h",
        status=ExperimentStatus.RUNNING,
    )

    # When / Then the unkeyed option's share can't be attributed, so rather than
    # folding it into control SRM is skipped entirely and the gap is logged
    assert services._expected_variant_shares(experiment) == {}
    assert log.has(
        "srm.unkeyed_variant",
        level="error",
        experiment__id=experiment.id,
        environment__id=experiment.environment_id,
        feature__id=experiment.feature_id,
    )


@pytest.mark.django_db
def test_expected_variant_shares__overallocated_options__returns_empty(
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given a misconfigured feature whose options allocate more than 100%
    feature = _multivariate_feature(environment, {"variant_a": 70, "variant_b": 60})
    experiment = Experiment.objects.create(
        environment=environment,
        feature=feature,
        name="exp",
        hypothesis="h",
        status=ExperimentStatus.RUNNING,
    )

    # When / Then control's share would be negative, so SRM is skipped and logged
    assert services._expected_variant_shares(experiment) == {}
    assert log.has(
        "srm.overallocated",
        level="error",
        experiment__id=experiment.id,
        environment__id=experiment.environment_id,
        feature__id=experiment.feature_id,
    )


@pytest.mark.django_db
def test_expected_variant_shares__no_multivariate_options__returns_empty(
    environment: Environment,
    feature: Feature,
) -> None:
    # Given a standard feature with no multivariate allocations
    experiment = Experiment.objects.create(
        environment=environment,
        feature=feature,
        name="exp",
        hypothesis="h",
        status=ExperimentStatus.RUNNING,
    )

    # When / Then there is no split to test
    assert services._expected_variant_shares(experiment) == {}


@pytest.mark.django_db
def test_expected_variant_shares__no_live_feature_state__returns_empty(
    experiment: Experiment,
) -> None:
    # Given the feature has no live state in the environment
    FeatureState.objects.filter(
        feature=experiment.feature,
        environment=experiment.environment,
    ).delete()

    # When / Then
    assert services._expected_variant_shares(experiment) == {}


@pytest.mark.django_db
def test_compute_results_summary__experiment__queries_warehouse_and_builds(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given a running experiment with one keyed variant and one attached metric
    feature = _multivariate_feature(environment, {"variant_a": 50})
    experiment = Experiment.objects.create(
        environment=environment,
        feature=feature,
        name="exp",
        hypothesis="h",
        status=ExperimentStatus.RUNNING,
    )
    metric = Metric.objects.create(
        environment=environment,
        name="Purchases",
        aggregation=MetricAggregation.OCCURRENCE,
        direction=MetricDirection.UP,
        definition={"version": 1, "event": "purchase"},
    )
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )
    expected_specs = [
        _spec(
            metric_id=metric.id,
            event="purchase",
            aggregation=MetricAggregation.OCCURRENCE,
        )
    ]
    aggregates = _aggregates(
        specs=expected_specs,
        exposure_counts={"control": 1000, "variant_a": 1000},
        metric_stats={
            metric.id: {
                "control": VariantStats(n=1000, sum=100.0, sum_squares=100.0),
                "variant_a": VariantStats(n=1000, sum=140.0, sum_squares=140.0),
            }
        },
    )
    mock_stats = mocker.patch(
        "experimentation.services.get_metric_variant_stats",
        return_value=aggregates,
    )
    window_start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    window_end = datetime(2026, 6, 10, tzinfo=timezone.utc)

    # When
    summary = services.compute_results_summary(
        experiment,
        window_start=window_start,
        window_end=window_end,
    )

    # Then the warehouse is queried with the experiment's metric specs
    mock_stats.assert_called_once_with(
        environment_key=environment.api_key,
        feature_name=feature.name,
        window_start=window_start,
        window_end=window_end,
        specs=expected_specs,
    )
    # And the summary carries the metric result with an SRM verdict from the
    # configured 50/50 split
    assert summary.srm_p_value == pytest.approx(1.0)
    assert summary.metrics[0].metric_id == metric.id
    assert summary.metrics[0].inference["variant_a"] is not None


def test_apply_experiment_rollout__no_segment__creates_segment_and_override(
    experiment: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
) -> None:
    # Given
    option_a, option_b, _ = multivariate_options

    # When
    services.apply_experiment_rollout(
        experiment,
        RolloutSpec(
            enabled=True,
            rollout_percentage=42.0,
            feature_state_value="control",
            value_type="string",
            multivariate_values=[
                MultivariateValueChangeSet(option_a.id, 60.0),
                MultivariateValueChangeSet(option_b.id, 40.0),
            ],
            author=AuthorData(user=admin_user),
        ),
    )

    # Then
    experiment.refresh_from_db()
    segment = experiment.rollout_segment
    assert segment is not None
    assert segment.is_system_segment is True
    condition = Condition.objects.get(rule__segment=segment)
    assert condition.operator == PERCENTAGE_SPLIT
    assert condition.value == "42.0"

    override = FeatureState.objects.get(
        environment=experiment.environment,
        feature=experiment.feature,
        feature_segment__segment=segment,
    )
    assert override.enabled is True
    allocations = {
        mv.multivariate_feature_option_id: mv.percentage_allocation
        for mv in override.multivariate_feature_state_values.all()
    }
    assert allocations == {option_a.id: 60.0, option_b.id: 40.0}


def test_apply_experiment_rollout__existing_segment__updates_percentage_and_enabled(
    experiment_with_rollout: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
) -> None:
    # Given
    experiment = experiment_with_rollout
    option_a, option_b, _ = multivariate_options

    # When
    services.apply_experiment_rollout(
        experiment,
        RolloutSpec(
            enabled=False,
            rollout_percentage=80.0,
            feature_state_value="control",
            value_type="string",
            multivariate_values=[
                MultivariateValueChangeSet(option_a.id, 50.0),
                MultivariateValueChangeSet(option_b.id, 50.0),
            ],
            author=AuthorData(user=admin_user),
        ),
    )

    # Then
    condition = Condition.objects.get(rule__segment=experiment.rollout_segment)
    assert condition.value == "80.0"
    override = FeatureState.objects.get(
        environment=experiment.environment,
        feature=experiment.feature,
        feature_segment__segment=experiment.rollout_segment,
    )
    assert override.enabled is False


def test_apply_experiment_rollout__completed__raises(
    experiment_with_rollout: Experiment,
    admin_user: FFAdminUser,
) -> None:
    # Given
    experiment = experiment_with_rollout
    experiment.status = ExperimentStatus.COMPLETED
    experiment.save()

    # When / Then
    with pytest.raises(ValidationError):
        services.apply_experiment_rollout(
            experiment,
            RolloutSpec(
                enabled=True,
                rollout_percentage=50.0,
                feature_state_value="control",
                value_type="string",
                multivariate_values=[],
                author=AuthorData(user=admin_user),
            ),
        )


@pytest.mark.parametrize(
    "status",
    [ExperimentStatus.RUNNING, ExperimentStatus.PAUSED],
)
def test_apply_experiment_rollout__running_or_paused__updates_rollout(
    status: ExperimentStatus,
    experiment_with_rollout: Experiment,
    admin_user: FFAdminUser,
) -> None:
    # Given
    experiment = experiment_with_rollout
    experiment.status = status
    experiment.save()

    # When
    services.apply_experiment_rollout(
        experiment,
        RolloutSpec(
            enabled=True,
            rollout_percentage=50.0,
            feature_state_value="control",
            value_type="string",
            multivariate_values=[],
            author=AuthorData(user=admin_user),
        ),
    )

    # Then
    condition = Condition.objects.get(rule__segment=experiment.rollout_segment)
    assert condition.value == "50.0"


def test_apply_experiment_rollout__duplicate_options__raises(
    experiment: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
) -> None:
    # Given
    option_a, _, _ = multivariate_options

    # When / Then
    with pytest.raises(ValidationError):
        services.apply_experiment_rollout(
            experiment,
            RolloutSpec(
                enabled=True,
                rollout_percentage=20.0,
                feature_state_value="control",
                value_type="string",
                multivariate_values=[
                    MultivariateValueChangeSet(option_a.id, 40.0),
                    MultivariateValueChangeSet(option_a.id, 60.0),
                ],
                author=AuthorData(user=admin_user),
            ),
        )


def test_apply_experiment_rollout__update_flag_fails__rolls_back(
    experiment_with_rollout: Experiment,
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given
    experiment = experiment_with_rollout
    mocker.patch(
        "experimentation.services.update_flag",
        side_effect=RuntimeError("boom"),
    )

    # When / Then
    with pytest.raises(RuntimeError):
        services.apply_experiment_rollout(
            experiment,
            RolloutSpec(
                enabled=False,
                rollout_percentage=80.0,
                feature_state_value="control",
                value_type="string",
                multivariate_values=[],
                author=AuthorData(user=admin_user),
            ),
        )

    # Then
    condition = Condition.objects.get(
        rule__segment=experiment.rollout_segment, operator=PERCENTAGE_SPLIT
    )
    assert condition.value == "20.0"


def _rollout_percentage_in_written_document(
    mock_dynamo_env_wrapper: MagicMock,
) -> str | None:
    environments = mock_dynamo_env_wrapper.write_environments.call_args[0][0]
    document = map_environment_to_environment_document(list(environments)[0])

    values: list[str] = []

    def _walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("operator") == PERCENTAGE_SPLIT:
                values.append(node.get("value"))  # type: ignore[arg-type]
            for child in node.values():
                _walk(child)
        elif isinstance(node, list):
            for child in node:
                _walk(child)

    _walk(document)
    return values[0] if values else None


def test_apply_experiment_rollout__update_under_v2__rebuilds_environment_document(  # type: ignore[no-untyped-def]
    environment_v2_versioning: Environment,
    multivariate_feature: Feature,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
    mocker: MockerFixture,
    django_capture_on_commit_callbacks,
) -> None:
    # Given
    mock_dynamo_env_wrapper = mocker.patch("environments.models.environment_wrapper")
    environment = environment_v2_versioning
    environment.project.enable_dynamo_db = True
    environment.project.save()

    option_a, option_b, _ = multivariate_options
    experiment = Experiment.objects.create(
        environment=environment,
        feature=multivariate_feature,
        name="exp",
        hypothesis="h",
        status=ExperimentStatus.RUNNING,
    )

    def _spec(rollout_percentage: float) -> RolloutSpec:
        return RolloutSpec(
            enabled=True,
            rollout_percentage=rollout_percentage,
            feature_state_value="control",
            value_type="string",
            multivariate_values=[
                MultivariateValueChangeSet(option_a.id, 50.0),
                MultivariateValueChangeSet(option_b.id, 50.0),
            ],
            author=AuthorData(user=admin_user),
        )

    with django_capture_on_commit_callbacks(execute=True):
        services.apply_experiment_rollout(experiment, _spec(20.0))
    experiment.refresh_from_db()

    assert _rollout_percentage_in_written_document(mock_dynamo_env_wrapper) == "20.0"

    # When
    mock_dynamo_env_wrapper.reset_mock()
    with django_capture_on_commit_callbacks(execute=True):
        services.apply_experiment_rollout(experiment, _spec(15.0))

    # Then
    assert mock_dynamo_env_wrapper.write_environments.called
    assert _rollout_percentage_in_written_document(mock_dynamo_env_wrapper) == "15.0"


def test_apply_experiment_rollout__update_under_v1__rebuilds_environment_document(  # type: ignore[no-untyped-def]
    environment: Environment,
    multivariate_feature: Feature,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
    mocker: MockerFixture,
    django_capture_on_commit_callbacks,
) -> None:
    # Given
    mock_dynamo_env_wrapper = mocker.patch("environments.models.environment_wrapper")
    environment.project.enable_dynamo_db = True
    environment.project.save()

    option_a, option_b, _ = multivariate_options
    experiment = Experiment.objects.create(
        environment=environment,
        feature=multivariate_feature,
        name="exp",
        hypothesis="h",
        status=ExperimentStatus.RUNNING,
    )

    def _spec(rollout_percentage: float) -> RolloutSpec:
        return RolloutSpec(
            enabled=True,
            rollout_percentage=rollout_percentage,
            feature_state_value="control",
            value_type="string",
            multivariate_values=[
                MultivariateValueChangeSet(option_a.id, 50.0),
                MultivariateValueChangeSet(option_b.id, 50.0),
            ],
            author=AuthorData(user=admin_user),
        )

    with django_capture_on_commit_callbacks(execute=True):
        services.apply_experiment_rollout(experiment, _spec(20.0))
    experiment.refresh_from_db()

    # When
    mock_dynamo_env_wrapper.reset_mock()
    with django_capture_on_commit_callbacks(execute=True):
        services.apply_experiment_rollout(experiment, _spec(15.0))

    # Then
    assert mock_dynamo_env_wrapper.write_environments.called
    assert _rollout_percentage_in_written_document(mock_dynamo_env_wrapper) == "15.0"


def test_get_experiment_rollout__rollout_exists__returns_representation(
    experiment_with_rollout: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
) -> None:
    # Given a rollout (20%, options split 50/50, value "control") from the fixture
    option_a, option_b, _ = multivariate_options

    # When
    rollout = services.get_experiment_rollout(experiment_with_rollout)

    # Then
    assert rollout is not None
    assert rollout["enabled"] is True
    assert rollout["rollout_percentage"] == 20.0
    assert rollout["feature_state_value"] == {"type": "string", "value": "control"}
    assert {
        (mv["multivariate_feature_option"], mv["percentage_allocation"])
        for mv in rollout["multivariate_feature_state_values"]
    } == {(option_a.id, 50.0), (option_b.id, 50.0)}


def test_get_experiment_rollout__no_rollout__returns_none(
    experiment: Experiment,
) -> None:
    # Given an experiment without a rollout
    # When / Then
    assert services.get_experiment_rollout(experiment) is None


def test_get_experiment_rollout__v2_versioning__returns_representation(
    environment_v2_versioning: Environment,
    multivariate_feature: Feature,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
) -> None:
    # Given a rollout on a v2 environment
    option_a, option_b, _ = multivariate_options
    experiment = Experiment.objects.create(
        environment=environment_v2_versioning,
        feature=multivariate_feature,
        name="exp",
        hypothesis="h",
        status=ExperimentStatus.CREATED,
    )
    services.apply_experiment_rollout(
        experiment,
        RolloutSpec(
            enabled=True,
            rollout_percentage=30.0,
            feature_state_value="control",
            value_type="string",
            multivariate_values=[
                MultivariateValueChangeSet(option_a.id, 60.0),
                MultivariateValueChangeSet(option_b.id, 40.0),
            ],
            author=AuthorData(user=admin_user),
        ),
    )

    # When
    rollout = services.get_experiment_rollout(experiment)

    # Then
    assert rollout is not None
    assert rollout["rollout_percentage"] == 30.0
    assert {
        (mv["multivariate_feature_option"], mv["percentage_allocation"])
        for mv in rollout["multivariate_feature_state_values"]
    } == {(option_a.id, 60.0), (option_b.id, 40.0)}


def test_get_experiment_rollout__boolean_value__returns_lowercase_string(
    experiment: Experiment,
    admin_user: FFAdminUser,
) -> None:
    # Given
    services.apply_experiment_rollout(
        experiment,
        RolloutSpec(
            enabled=True,
            rollout_percentage=20.0,
            feature_state_value="true",
            value_type="boolean",
            multivariate_values=[],
            author=AuthorData(user=admin_user),
        ),
    )

    # When
    rollout = services.get_experiment_rollout(experiment)

    # Then
    assert rollout is not None
    assert rollout["feature_state_value"] == {"type": "boolean", "value": "true"}


def test_enable_experiment_rollout__disabled_rollout__enables_and_preserves_allocations(
    experiment: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
) -> None:
    # Given a disabled rollout with a 50/50 multivariate split
    option_a, option_b, _ = multivariate_options
    services.apply_experiment_rollout(
        experiment,
        RolloutSpec(
            enabled=False,
            rollout_percentage=20.0,
            feature_state_value="control",
            value_type="string",
            multivariate_values=[
                MultivariateValueChangeSet(option_a.id, 50.0),
                MultivariateValueChangeSet(option_b.id, 50.0),
            ],
            author=AuthorData(user=admin_user),
        ),
    )

    # When
    services.enable_experiment_rollout(experiment, AuthorData(user=admin_user))

    # Then the override is enabled with its allocations preserved
    rollout = services.get_experiment_rollout(experiment)
    assert rollout is not None
    assert rollout["enabled"] is True
    assert {
        (mv["multivariate_feature_option"], mv["percentage_allocation"])
        for mv in rollout["multivariate_feature_state_values"]
    } == {(option_a.id, 50.0), (option_b.id, 50.0)}


def test_enable_experiment_rollout__already_enabled__no_op(
    experiment_with_rollout: Experiment,
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given a rollout that is already enabled
    update_flag = mocker.patch("experimentation.services.update_flag")

    # When
    services.enable_experiment_rollout(
        experiment_with_rollout, AuthorData(user=admin_user)
    )

    # Then no flag write is made
    update_flag.assert_not_called()


def test_enable_experiment_rollout__no_rollout__no_op(
    experiment: Experiment,
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given an experiment without a rollout
    update_flag = mocker.patch("experimentation.services.update_flag")

    # When
    services.enable_experiment_rollout(experiment, AuthorData(user=admin_user))

    # Then nothing is written
    update_flag.assert_not_called()


def test_apply_experiment_rollout__reapplied_under_v2__keeps_variant_assignment(
    environment_v2_versioning: Environment,
    multivariate_feature: Feature,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
) -> None:
    # Given a running experiment whose rollout splits two variants 50/50
    option_a, option_b, _ = multivariate_options
    experiment = Experiment.objects.create(
        environment=environment_v2_versioning,
        feature=multivariate_feature,
        name="exp",
        hypothesis="h",
        status=ExperimentStatus.RUNNING,
    )
    spec = RolloutSpec(
        enabled=True,
        rollout_percentage=50.0,
        feature_state_value="control",
        value_type="string",
        multivariate_values=[
            MultivariateValueChangeSet(option_a.id, 50.0),
            MultivariateValueChangeSet(option_b.id, 50.0),
        ],
        author=AuthorData(user=admin_user),
    )
    identity_hash_keys = [f"identity-{i}" for i in range(50)]

    def variant_assignment() -> dict[str, int]:
        override = (
            FeatureState.objects.get_live_feature_states(
                environment=experiment.environment,
                additional_filters=Q(
                    feature_segment__segment=experiment.rollout_segment,
                    identity__isnull=True,
                ),
                feature_id=experiment.feature_id,
            )
            .prefetch_related(
                "multivariate_feature_state_values__multivariate_feature_option"
            )
            .latest("id")
        )
        assignment: dict[str, int] = {}
        for key in identity_hash_keys:
            option = override.get_multivariate_feature_state_value(key)
            # The 50/50 split allocates 100%, so every identity lands on an option.
            assert isinstance(option, MultivariateFeatureOption)
            assignment[key] = option.id
        return assignment

    # When the rollout is applied, then re-applied unchanged (e.g. tuned while
    # the experiment is running)
    services.apply_experiment_rollout(experiment, spec)
    experiment.refresh_from_db()
    before = variant_assignment()

    services.apply_experiment_rollout(experiment, spec)
    after = variant_assignment()

    # Then every already-enrolled identity keeps the variant it was first
    # assigned; tuning the rollout must not re-randomise the split.
    assert before == after
