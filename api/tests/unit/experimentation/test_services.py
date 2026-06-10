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
    VariantExposures,
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
    # Given the warehouse returns one bucket row per variant per day
    # (aware datetimes: the bucket column type carries 'UTC')
    rows = [
        ("control", datetime(2026, 6, 1, tzinfo=timezone.utc), 100),
        ("variant_a", datetime(2026, 6, 1, tzinfo=timezone.utc), 90),
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
    ]
    # And the query buckets first exposures by UTC day, deduplicates
    # identities, and quarantines identities seen in more than one variant
    sql, params = mock_client.execute.call_args.args
    assert "toStartOfDay(first_exposure, 'UTC') AS bucket" in sql
    assert "GROUP BY identifier" in sql
    assert "uniqExact(value) > 1" in sql
    assert params == {
        "environment_key": "env-key-123",
        "exposure_event": "$flag_exposure",
        "feature_name": "my-feature",
        "multiple_variant": "$multiple",
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
        ("control", datetime(2026, 6, 1, tzinfo=timezone.utc), 10)
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
    assert summary.total_identities == 10


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
    assert summary.total_identities == 0


def _bucket(
    variant: str,
    bucket: datetime,
    first_exposed_identities: int,
) -> ExposureBucket:
    return ExposureBucket(
        variant=variant,
        bucket=bucket,
        first_exposed_identities=first_exposed_identities,
    )


def test_build_exposures_summary__multiple_variants__derives_totals() -> None:
    # Given two variants accumulating identities over two daily buckets
    day_1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
    day_2 = datetime(2026, 6, 2, tzinfo=timezone.utc)
    buckets = [
        _bucket("control", day_1, 100),
        _bucket("variant_a", day_1, 90),
        _bucket("control", day_2, 50),
        _bucket("variant_a", day_2, 70),
    ]

    # When
    summary = services.build_exposures_summary(
        buckets,
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 10, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then
    assert summary.total_identities == 310
    assert summary.excluded_identities == 0
    assert summary.days_of_data == 9
    assert summary.variants == [
        VariantExposures(key="control", identities=150, is_control=True),
        VariantExposures(key="variant_a", identities=160, is_control=False),
    ]


def test_build_exposures_summary__control_not_largest__still_listed_first() -> None:
    # Given a control variant with fewer identities than two treatments
    day = datetime(2026, 6, 1, tzinfo=timezone.utc)
    buckets = [
        _bucket("variant_b", day, 30),
        _bucket("variant_a", day, 20),
        _bucket("control", day, 10),
    ]

    # When
    summary = services.build_exposures_summary(
        buckets,
        window_start=day,
        window_end=datetime(2026, 6, 8, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then control comes first, treatments follow by descending identities
    assert [v.key for v in summary.variants] == [
        "control",
        "variant_b",
        "variant_a",
    ]


def test_build_exposures_summary__tied_treatments__ordered_by_key() -> None:
    # Given two treatments with the same identity count
    day = datetime(2026, 6, 1, tzinfo=timezone.utc)
    buckets = [
        _bucket("variant_b", day, 30),
        _bucket("variant_a", day, 30),
    ]

    # When
    summary = services.build_exposures_summary(
        buckets,
        window_start=day,
        window_end=datetime(2026, 6, 8, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then the tie is broken alphabetically
    assert [v.key for v in summary.variants] == ["variant_a", "variant_b"]


def test_build_exposures_summary__multiple_sentinel__excluded_and_counted() -> None:
    # Given identities seen in more than one variant, quarantined as $multiple
    day = datetime(2026, 6, 1, tzinfo=timezone.utc)
    buckets = [
        _bucket("control", day, 100),
        _bucket("variant_a", day, 95),
        _bucket("$multiple", day, 5),
    ]

    # When
    summary = services.build_exposures_summary(
        buckets,
        window_start=day,
        window_end=datetime(2026, 6, 8, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then they are excluded from variants, the total and the timeseries
    assert summary.total_identities == 195
    assert summary.excluded_identities == 5
    assert [v.key for v in summary.variants] == ["control", "variant_a"]
    assert all(
        set(point.cumulative_identities) == {"control", "variant_a"}
        for point in summary.timeseries.points
    )


def test_build_exposures_summary__sparse_buckets__cumulative_carries_forward() -> None:
    # Given variants whose identities arrive in different buckets
    day_1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
    day_2 = datetime(2026, 6, 2, tzinfo=timezone.utc)
    buckets = [
        _bucket("control", day_1, 10),
        _bucket("variant_a", day_2, 7),
    ]

    # When
    summary = services.build_exposures_summary(
        buckets,
        window_start=day_1,
        window_end=datetime(2026, 6, 3, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then every point covers every variant, carrying totals forward
    assert summary.timeseries == ExposuresTimeseries(
        granularity="day",
        points=[
            ExposuresTimeseriesPoint(
                bucket="2026-06-01T00:00:00+00:00",
                cumulative_identities={"control": 10, "variant_a": 0},
            ),
            ExposuresTimeseriesPoint(
                bucket="2026-06-02T00:00:00+00:00",
                cumulative_identities={"control": 10, "variant_a": 7},
            ),
        ],
    )


def test_build_exposures_summary__no_buckets__empty_summary() -> None:
    # Given no exposure data
    # When
    summary = services.build_exposures_summary(
        [],
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 2, tzinfo=timezone.utc),
        granularity="hour",
    )

    # Then the summary is empty but fully shaped
    assert summary == ExposuresSummary(
        total_identities=0,
        excluded_identities=0,
        days_of_data=1,
        variants=[],
        timeseries=ExposuresTimeseries(granularity="hour", points=[]),
    )


def test_build_exposures_summary__partial_day_window__days_rounded_up() -> None:
    # Given a window of 3 days and 6 hours
    day = datetime(2026, 6, 1, tzinfo=timezone.utc)

    # When
    summary = services.build_exposures_summary(
        [],
        window_start=day,
        window_end=datetime(2026, 6, 4, 6, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then the partial day counts as a full one
    assert summary.days_of_data == 4


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
