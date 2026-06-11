from datetime import datetime, timezone

import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.models import Environment
from experimentation import services
from experimentation.dataclasses import (
    ExposureBucket,
    ExposuresSummary,
    ExposuresTimeseries,
    ExposuresTimeseriesPoint,
    WarehouseEventStats,
)
from experimentation.models import (
    WarehouseConnection,
    WarehouseConnectionStatus,
    WarehouseType,
)


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
