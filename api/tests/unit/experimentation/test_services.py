from dataclasses import asdict, replace
from datetime import datetime, timezone
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from django.db import IntegrityError, connection
from django.db.models import Q
from django.test.utils import CaptureQueriesContext
from flag_engine.segments.constants import EQUAL, PERCENTAGE_SPLIT
from prometheus_client import REGISTRY
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from rest_framework.exceptions import ValidationError

from api_keys.models import MasterAPIKey
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from cohorts.models import CohortMembership, CohortSourceType
from cohorts.services import apply_pending_memberships, create_cohort
from core.dataclasses import AuthorData
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from experimentation import services
from experimentation.constants import MAX_AUDIENCE_SEGMENTS
from experimentation.dataclasses import (
    AudienceSpec,
    ConversionBucket,
    ConversionsTimeseries,
    ConversionsTimeseriesPoint,
    ExposureBucket,
    ExposuresSummary,
    ExposuresTimeseries,
    ExposuresTimeseriesPoint,
    MetricSpec,
    ResultsAggregates,
    RolloutSpec,
    WarehouseEventNames,
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
from experimentation.results_query import ResultsQueryBuilder, _MetricSlot
from experimentation.services import (
    annotate_warehouse_event_stats,
    verify_clickhouse_connection,
)
from experimentation.stats import VariantStats
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import STRING
from features.versioning.dataclasses import MultivariateValueChangeSet
from organisations.models import Organisation
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from tests.unit.experimentation.conftest import RolloutSpecFactory
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
        client_name=settings.CLICKHOUSE_CONNECTION_CLIENT_NAME,
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
        client_name=settings.CLICKHOUSE_CONNECTION_CLIENT_NAME,
    )
    services._get_clickhouse_client.cache_clear()


def test_get_clickhouse_client__per_timeout__caches_distinct_clients(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.EXPERIMENTATION_CLICKHOUSE_URL = "clickhouse://ch.example.com/db"
    mock_client_cls = mocker.patch(
        "experimentation.services.Client",
        side_effect=lambda *args, **kwargs: mocker.Mock(),
    )
    services._get_clickhouse_client.cache_clear()

    # When
    client = services._get_clickhouse_client()
    same_client = services._get_clickhouse_client()
    background_client = services._get_clickhouse_client(
        send_receive_timeout=services.CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS,
    )

    # Then
    assert client is same_client
    assert background_client is not client
    assert mock_client_cls.call_count == 2
    assert (
        mock_client_cls.call_args_list[1].kwargs["send_receive_timeout"]
        == services.CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS
    )
    services._get_clickhouse_client.cache_clear()


@pytest.mark.parametrize(
    "rows, expected",
    [
        (
            [("conversion",), ("page_view",)],
            WarehouseEventNames(events=["conversion", "page_view"], is_truncated=False),
        ),
        ([], WarehouseEventNames(events=[], is_truncated=False)),
        (
            [(f"event_{i:03d}",) for i in range(501)],
            WarehouseEventNames(
                events=[f"event_{i:03d}" for i in range(500)], is_truncated=True
            ),
        ),
    ],
    ids=["few", "none", "truncated"],
)
def test_get_warehouse_event_names__flagsmith_connection__returns_capped_names(
    warehouse_connection: WarehouseConnection,
    settings: SettingsWrapper,
    reset_cache: None,
    rows: list[tuple[str]],
    expected: WarehouseEventNames,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.EXPERIMENTATION_CLICKHOUSE_URL = "clickhouse://ch.example.com/db"
    mock_client = mocker.Mock()
    mock_client.execute.return_value = rows
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )

    # When
    result = services.get_warehouse_event_names(warehouse_connection, "env-key-123")

    # Then
    assert result == expected
    mock_client.execute.assert_called_once_with(
        "SELECT event FROM events "
        "WHERE environment_key = %(environment_key)s "
        "GROUP BY event ORDER BY max(timestamp) DESC LIMIT %(limit)s",
        {"environment_key": "env-key-123", "limit": 501},
    )

    # When — the result is cached, so a second request doesn't hit the warehouse
    second_result = services.get_warehouse_event_names(
        warehouse_connection, "env-key-123"
    )

    # Then
    mock_client.execute.assert_called_once()
    assert second_result == expected


@pytest.mark.parametrize(
    "clickhouse_url, execute_side_effect",
    [
        ("", None),
        ("clickhouse://ch.example.com/db", Exception("connection refused")),
    ],
    ids=["unconfigured", "unreachable"],
)
def test_get_warehouse_event_names__flagsmith_warehouse_unavailable__returns_none(
    warehouse_connection: WarehouseConnection,
    settings: SettingsWrapper,
    reset_cache: None,
    clickhouse_url: str,
    execute_side_effect: Exception | None,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.EXPERIMENTATION_CLICKHOUSE_URL = clickhouse_url
    mock_client = mocker.Mock()
    mock_client.execute.side_effect = execute_side_effect
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )

    # When
    result = services.get_warehouse_event_names(warehouse_connection, "env-key-123")

    # Then
    assert result is None
    assert any(
        event["event"] == "connection.event_names_failed" for event in log.events
    ) == (execute_side_effect is not None)


@pytest.mark.parametrize(
    "query_result, expected",
    [
        (
            [("conversion",), ("page_view",)],
            WarehouseEventNames(events=["conversion", "page_view"], is_truncated=False),
        ),
        (Exception("connection refused"), None),
    ],
    ids=["reachable", "unreachable"],
)
def test_get_warehouse_event_names__clickhouse_connection__queries_customer_instance(
    clickhouse_connection: WarehouseConnection,
    reset_cache: None,
    query_result: Exception | list[tuple[str]],
    expected: WarehouseEventNames | None,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given
    get_client = mocker.patch(
        "experimentation.warehouse_delivery_service.clickhouse_connect.get_client",
    )
    if isinstance(query_result, Exception):
        get_client.return_value.query.side_effect = query_result
    else:
        get_client.return_value.query.return_value = mocker.Mock(
            result_rows=query_result
        )

    # When
    result = services.get_warehouse_event_names(clickhouse_connection, "test-env-key")

    # Then
    assert result == expected
    get_client.return_value.query.assert_called_once_with(
        "SELECT event FROM events "
        "WHERE environment_key = %(environment_key)s "
        "GROUP BY event ORDER BY max(timestamp) DESC LIMIT %(limit)s",
        parameters={"environment_key": "test-env-key", "limit": 501},
    )
    get_client.return_value.close.assert_called_once_with()
    assert any(
        event["event"] == "connection.event_names_failed" for event in log.events
    ) == (expected is None)

    # When — the outcome is cached, so a second request doesn't reconnect
    fresh_connection = WarehouseConnection.objects.get(id=clickhouse_connection.id)
    second_result = services.get_warehouse_event_names(fresh_connection, "test-env-key")

    # Then
    get_client.assert_called_once()
    assert second_result == expected


@pytest.mark.parametrize(
    "changed_field, new_value, expected_events, expected_query_count",
    [
        ("config", {"host": "new.acme-corp.example"}, ["new_event"], 2),
        ("credentials", {"password": "rotated"}, ["old_event"], 1),
    ],
    ids=["config-bypasses-cache", "credentials-keep-cache"],
)
def test_get_warehouse_event_names__connection_details_changed__cache_keyed_by_config(
    clickhouse_connection: WarehouseConnection,
    reset_cache: None,
    changed_field: str,
    new_value: dict[str, str],
    expected_events: list[str],
    expected_query_count: int,
    mocker: MockerFixture,
) -> None:
    # Given — a cached result for the connection's current details
    get_client = mocker.patch(
        "experimentation.warehouse_delivery_service.clickhouse_connect.get_client",
    )
    get_client.return_value.query.return_value = mocker.Mock(
        result_rows=[("old_event",)]
    )
    services.get_warehouse_event_names(clickhouse_connection, "test-env-key")

    # When — the connection details change
    setattr(
        clickhouse_connection,
        changed_field,
        {**getattr(clickhouse_connection, changed_field), **new_value},
    )
    clickhouse_connection.save()
    get_client.return_value.query.return_value = mocker.Mock(
        result_rows=[("new_event",)]
    )
    result = services.get_warehouse_event_names(clickhouse_connection, "test-env-key")

    # Then — a config change re-queries; a credential rotation keeps the cache
    assert result == WarehouseEventNames(events=expected_events, is_truncated=False)
    assert get_client.return_value.query.call_count == expected_query_count


def test_get_warehouse_event_names__unsupported_type__raises(
    environment: Environment,
) -> None:
    # Given
    connection = WarehouseConnection(
        environment=environment,
        warehouse_type=WarehouseType.SNOWFLAKE,
        name="Snowflake",
        config={"account_identifier": "acme"},
    )

    # When / Then
    with pytest.raises(ValueError, match="Unsupported warehouse type"):
        services.get_warehouse_event_names(connection, "test-env-key")


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
    mock_get_client = mocker.patch(
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
    mock_get_client.assert_called_once_with(
        send_receive_timeout=services.CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS,
    )


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
        granularity="day",
        exposure_buckets=[],
        conversion_buckets={},
    )


def _result_columns(metric_count: int) -> list[tuple[str, str]]:
    """The `(name, type)` metadata clickhouse-driver returns for the results
    query with `with_column_types=True`, in SELECT order."""
    columns = [("variant", "String"), ("n", "UInt64")]
    for i in range(metric_count):
        columns.append((f"m{i}_sum", "Float64"))
        columns.append((f"m{i}_sum_squares", "Float64"))
    return columns


def _conversion_columns() -> list[tuple[str, str]]:
    """Column metadata for the conversions query, in SELECT order."""
    return [
        ("variant", "String"),
        ("metric_index", "UInt8"),
        ("bucket", "DateTime('UTC')"),
        ("converted_identities", "UInt64"),
    ]


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
    mock_client.execute.side_effect = [
        (rows, _result_columns(4)),
        ([], _conversion_columns()),
        [],
    ]
    mock_get_client = mocker.patch(
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
    aggregates = services.get_results_aggregates(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=window_start,
        window_end=window_end,
        specs=specs,
        granularity="day",
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
    # And the results query joins post-exposure metric events and excludes
    # quarantined identities
    sql, params = mock_client.execute.call_args_list[0].args
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
    # And the conversions join is narrowed to the occurrence metric's event
    assert params["conversion_events"] == ["purchase"]
    mock_get_client.assert_called_with(
        send_receive_timeout=services.CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS,
    )


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
    mock_client.execute.side_effect = [
        (rows, _result_columns(2)),
        ([], _conversion_columns()),
        [],
    ]
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )
    specs = [
        _spec(metric_id=7, event="purchase", aggregation=MetricAggregation.OCCURRENCE),
        _spec(metric_id=9, event="revenue", aggregation=MetricAggregation.SUM),
    ]

    # When
    aggregates = services.get_results_aggregates(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 10, tzinfo=timezone.utc),
        specs=specs,
        granularity="day",
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
    mock_client.execute.side_effect = [
        ([("control", 1000), ("variant_a", 900)], _result_columns(0)),
        [],
    ]
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )

    # When
    aggregates = services.get_results_aggregates(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 10, tzinfo=timezone.utc),
        specs=[],
        granularity="day",
    )

    # Then only the per-variant counts are returned, with no metric join, and
    # no conversions query is run
    assert aggregates.exposure_counts == {"control": 1000, "variant_a": 900}
    assert aggregates.metric_stats == {}
    assert aggregates.conversion_buckets == {}
    assert mock_client.execute.call_count == 2
    sql, params = mock_client.execute.call_args_list[0].args
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
    mock_client.execute.side_effect = [
        (rows, columns),
        ([], _conversion_columns()),
        [],
    ]
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )
    specs = [
        _spec(metric_id=7, event="purchase", aggregation=MetricAggregation.OCCURRENCE),
        _spec(metric_id=9, event="revenue", aggregation=MetricAggregation.SUM),
    ]

    # When
    aggregates = services.get_results_aggregates(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 10, tzinfo=timezone.utc),
        specs=specs,
        granularity="day",
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


def test_build_conversions_query__mixed_slots__occurrence_slots_only() -> None:
    # Given an occurrence metric, a sum metric and a second occurrence metric
    builder = ResultsQueryBuilder(
        [
            _spec(metric_id=7, event="purchase", aggregation="occurrence"),
            _spec(metric_id=9, event="revenue", aggregation="sum"),
            _spec(metric_id=11, event="signup", aggregation="occurrence"),
        ]
    )

    # When
    sql = builder.build_conversions_query(bucket_function="toStartOfDay")

    # Then each occurrence slot records the identity's first post-exposure
    # conversion, with the same attribution condition as the results query
    assert sql is not None
    assert (
        "minIfOrNull(m.timestamp, m.event = %(metric_0_event)s"
        " AND m.timestamp >= e.first_exposure) AS c0" in sql
    )
    assert (
        "minIfOrNull(m.timestamp, m.event = %(metric_2_event)s"
        " AND m.timestamp >= e.first_exposure) AS c2" in sql
    )
    assert " AS c1" not in sql
    # And conversions are counted per slot per UTC bucket, skipping identities
    # that never converted and identities seen in more than one variant
    assert "ARRAY JOIN [0, 2] AS metric_index, [c0, c2] AS first_conversion" in sql
    assert "toStartOfDay(first_conversion, 'UTC') AS bucket" in sql
    assert "WHERE first_conversion IS NOT NULL" in sql
    assert "GROUP BY variant, metric_index, bucket" in sql
    assert "WHERE e.quarantined = 0" in sql
    # And the join is narrowed to the charted metrics' events
    assert "AND m.event IN %(conversion_events)s" in sql


def test_build_conversions_query__no_occurrence_slots__returns_none() -> None:
    # Given only value metrics, which have no conversion rate to chart
    builder = ResultsQueryBuilder(
        [
            _spec(metric_id=9, event="revenue", aggregation="sum"),
            _spec(metric_id=13, event="session", aggregation="mean"),
        ]
    )

    # When / Then
    assert builder.build_conversions_query(bucket_function="toStartOfDay") is None


def test_decode_conversion_rows__rows__groups_by_metric_behind_slot_index() -> None:
    # Given occurrence slots at index 0 and 2, rows for slot 0 only, and
    # columns in a different order than the SELECT
    builder = ResultsQueryBuilder(
        [
            _spec(metric_id=7, event="purchase", aggregation="occurrence"),
            _spec(metric_id=9, event="revenue", aggregation="sum"),
            _spec(metric_id=11, event="signup", aggregation="occurrence"),
        ]
    )
    bucket = datetime(2026, 6, 1, tzinfo=timezone.utc)
    columns = ["converted_identities", "variant", "bucket", "metric_index"]
    rows = [(12, "control", bucket, 0), (3, "variant_a", bucket, 0)]

    # When
    buckets = builder.decode_conversion_rows(rows, columns)

    # Then rows are decoded by column name under the metric behind their slot,
    # and the charted metric nobody converted on still gets an empty entry
    assert buckets == {
        7: [
            ConversionBucket("control", bucket, converted_identities=12),
            ConversionBucket("variant_a", bucket, converted_identities=3),
        ],
        11: [],
    }


def test_get_results_aggregates__occurrence_metric__gathers_chart_rows(
    mocker: MockerFixture,
) -> None:
    # Given the warehouse answers the results query, then one conversion row
    # per variant for the occurrence metric in slot 0, then one exposure row
    bucket = datetime(2026, 6, 1, tzinfo=timezone.utc)
    mock_client = mocker.Mock()
    mock_client.execute.side_effect = [
        ([("control", 1000, 12.0, 12.0, 500.0, 900.0)], _result_columns(2)),
        (
            [("control", 0, bucket, 12), ("variant_a", 0, bucket, 15)],
            _conversion_columns(),
        ),
        [(0, "control", bucket, 1000)],
    ]
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )
    specs = [
        _spec(metric_id=7, event="purchase", aggregation="occurrence"),
        _spec(metric_id=9, event="revenue", aggregation="sum"),
    ]
    window_start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    window_end = datetime(2026, 6, 10, tzinfo=timezone.utc)

    # When
    aggregates = services.get_results_aggregates(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=window_start,
        window_end=window_end,
        specs=specs,
        granularity="day",
    )

    # Then the chart rows are mapped, conversions under the occurrence metric only
    assert aggregates.granularity == "day"
    assert aggregates.conversion_buckets == {
        7: [
            ConversionBucket("control", bucket, converted_identities=12),
            ConversionBucket("variant_a", bucket, converted_identities=15),
        ]
    }
    assert aggregates.exposure_buckets == [
        ExposureBucket("control", bucket, first_exposed_identities=1000)
    ]
    # And the conversions query buckets first conversions by UTC day, joining
    # only the occurrence metric's events over the results query's window
    sql, params = mock_client.execute.call_args_list[1].args
    assert "toStartOfDay(first_conversion, 'UTC') AS bucket" in sql
    assert params == {
        "environment_key": "env-key-123",
        "exposure_event": "$flag_exposure",
        "feature_name": "my-feature",
        "window_start": window_start,
        "window_end": window_end,
        "metric_events": ["purchase", "revenue"],
        "conversion_events": ["purchase"],
        "metric_0_event": "purchase",
        "metric_1_event": "revenue",
    }


def test_get_results_aggregates__value_metrics_only__skips_conversions_query(
    mocker: MockerFixture,
) -> None:
    # Given only a value metric is attached
    mock_client = mocker.Mock()
    mock_client.execute.side_effect = [
        ([("control", 1000, 500.0, 900.0)], _result_columns(1)),
        [],
    ]
    mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )

    # When
    aggregates = services.get_results_aggregates(
        environment_key="env-key-123",
        feature_name="my-feature",
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 10, tzinfo=timezone.utc),
        specs=[_spec(metric_id=9, event="revenue", aggregation="sum")],
        granularity="day",
    )

    # Then nothing is charted and only the results and exposures queries run
    assert aggregates.conversion_buckets == {}
    assert mock_client.execute.call_count == 2
    _, params = mock_client.execute.call_args_list[0].args
    assert params["conversion_events"] == []


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
    # And the chart series sit alongside, empty for a run with no bucket rows
    assert payload["exposures_timeseries"] == {"granularity": "day", "points": []}
    assert payload["metrics"][0]["conversions_timeseries"] is None


def test_build_results_summary__exposure_rows__attaches_exposures_timeseries() -> None:
    # Given exposure bucket rows arriving unordered, with a quarantined row
    day_1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
    day_3 = datetime(2026, 6, 3, tzinfo=timezone.utc)
    aggregates = ResultsAggregates(
        specs=[],
        exposure_counts={"control": 1000, "variant_a": 1000},
        metric_stats={},
        granularity="day",
        exposure_buckets=[
            ExposureBucket("control", day_3, first_exposed_identities=400),
            ExposureBucket("control", day_1, first_exposed_identities=600),
            ExposureBucket("variant_a", day_1, first_exposed_identities=1000),
            ExposureBucket("", day_1, first_exposed_identities=5, quarantined=True),
        ],
        conversion_buckets={},
    )

    # When
    summary = services.build_results_summary(aggregates, expected_shares={})

    # Then the chart denominator is bucketed in order, quarantined identities
    # left out
    assert summary.exposures_timeseries == ExposuresTimeseries(
        granularity="day",
        points=[
            ExposuresTimeseriesPoint(
                bucket=day_1.isoformat(),
                new_identities={"control": 600, "variant_a": 1000},
            ),
            ExposuresTimeseriesPoint(
                bucket=day_3.isoformat(),
                new_identities={"control": 400},
            ),
        ],
    )


def test_build_results_summary__occurrence_metrics__attach_conversions() -> None:
    # Given conversion rows for two occurrence metrics, arriving unordered
    day_1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
    day_3 = datetime(2026, 6, 3, tzinfo=timezone.utc)
    aggregates = ResultsAggregates(
        specs=[
            _spec(metric_id=7, event="purchase"),
            _spec(metric_id=11, event="signup"),
        ],
        exposure_counts={"control": 1000, "variant_a": 1000},
        metric_stats={},
        granularity="day",
        exposure_buckets=[],
        conversion_buckets={
            7: [
                ConversionBucket("variant_a", day_3, converted_identities=20),
                ConversionBucket("control", day_1, converted_identities=100),
                ConversionBucket("variant_a", day_1, converted_identities=100),
            ],
            11: [ConversionBucket("control", day_1, converted_identities=7)],
        },
    )

    # When
    summary = services.build_results_summary(aggregates, expected_shares={})

    # Then each metric gets only its own rows, per variant, in bucket order
    assert summary.metrics[0].conversions_timeseries == ConversionsTimeseries(
        granularity="day",
        points=[
            ConversionsTimeseriesPoint(
                bucket=day_1.isoformat(),
                converted_identities={"control": 100, "variant_a": 100},
            ),
            ConversionsTimeseriesPoint(
                bucket=day_3.isoformat(),
                converted_identities={"variant_a": 20},
            ),
        ],
    )
    assert summary.metrics[1].conversions_timeseries == ConversionsTimeseries(
        granularity="day",
        points=[
            ConversionsTimeseriesPoint(
                bucket=day_1.isoformat(),
                converted_identities={"control": 7},
            ),
        ],
    )


def test_build_results_summary__value_metric__timeseries_none() -> None:
    # Given a sum metric in a run that gathered bucket rows
    aggregates = ResultsAggregates(
        specs=[_spec(metric_id=9, event="revenue", aggregation="sum")],
        exposure_counts={"control": 1000},
        metric_stats={},
        granularity="day",
        exposure_buckets=[],
        conversion_buckets={},
    )

    # When
    summary = services.build_results_summary(aggregates, expected_shares={})

    # Then a value metric has no conversion rate to chart
    assert summary.metrics[0].conversions_timeseries is None


def test_build_results_summary__occurrence_metric_no_conversions__empty_series() -> (
    None
):
    # Given an occurrence metric that was charted but nobody converted on yet
    aggregates = ResultsAggregates(
        specs=[_spec(metric_id=7, event="purchase")],
        exposure_counts={"control": 1000},
        metric_stats={},
        granularity="day",
        exposure_buckets=[],
        conversion_buckets={7: []},
    )

    # When
    summary = services.build_results_summary(aggregates, expected_shares={})

    # Then the chart is present and empty, not absent
    assert summary.metrics[0].conversions_timeseries == ConversionsTimeseries(
        granularity="day", points=[]
    )


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
    window_start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    window_end = datetime(2026, 6, 10, tzinfo=timezone.utc)
    mock_gather = mocker.patch(
        "experimentation.services.get_results_aggregates",
        return_value=replace(
            aggregates,
            exposure_buckets=[
                ExposureBucket("control", window_start, first_exposed_identities=1000)
            ],
            conversion_buckets={
                metric.id: [
                    ConversionBucket("control", window_start, converted_identities=100)
                ]
            },
        ),
    )

    # When
    summary = services.compute_results_summary(
        experiment,
        window_start=window_start,
        window_end=window_end,
    )

    # Then the warehouse is read once for the experiment's metric specs,
    # bucketed by day because the window is longer than 72 hours
    mock_gather.assert_called_once_with(
        environment_key=environment.api_key,
        feature_name=feature.name,
        window_start=window_start,
        window_end=window_end,
        specs=expected_specs,
        granularity="day",
    )
    # And the summary carries the metric result with an SRM verdict from the
    # configured 50/50 split, plus both chart series
    assert summary.srm_p_value == pytest.approx(1.0)
    assert summary.metrics[0].metric_id == metric.id
    assert summary.metrics[0].inference["variant_a"] is not None
    assert summary.exposures_timeseries == ExposuresTimeseries(
        granularity="day",
        points=[
            ExposuresTimeseriesPoint(
                bucket=window_start.isoformat(), new_identities={"control": 1000}
            )
        ],
    )
    assert summary.metrics[0].conversions_timeseries == ConversionsTimeseries(
        granularity="day",
        points=[
            ConversionsTimeseriesPoint(
                bucket=window_start.isoformat(), converted_identities={"control": 100}
            )
        ],
    )


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
    assert segment.rules_data == [
        {
            "type": SegmentRule.ALL_RULE,
            "conditions": [
                {
                    "property": "$.identity.key",
                    "operator": PERCENTAGE_SPLIT,
                    "value": "42.0",
                    "description": None,
                }
            ],
            "rules": [],
        }
    ]

    # TODO: Drop the legacy rows as per https://github.com/Flagsmith/flagsmith/issues/7818
    assert _rules_from_orm(segment) == segment.rules_data

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


def test_apply_experiment_rollout__null_default_value__serialised_as_empty_string(
    experiment: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
) -> None:
    # Given the environment default has no value stored
    option_a, option_b, _ = multivariate_options
    default_state = FeatureState.objects.get(
        environment=experiment.environment,
        feature=experiment.feature,
        feature_segment__isnull=True,
        identity__isnull=True,
    )
    default_state.feature_state_value.string_value = None
    default_state.feature_state_value.save()

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

    # Then the default value is not rewritten as the string "None"
    default_state.refresh_from_db()
    assert default_state.get_feature_state_value() == ""


def test_apply_experiment_rollout__first_rollout__zeroes_default_allocations(
    experiment: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
) -> None:
    # Given
    option_a, option_b, option_c = multivariate_options

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
    default_state = FeatureState.objects.get(
        environment=experiment.environment,
        feature=experiment.feature,
        feature_segment__isnull=True,
        identity__isnull=True,
    )
    default_allocations = {
        mv.multivariate_feature_option_id: mv.percentage_allocation
        for mv in default_state.multivariate_feature_state_values.all()
    }
    assert default_allocations == {option_a.id: 0, option_b.id: 0, option_c.id: 0}

    # The rollout segment override keeps the experiment's own split.
    override = FeatureState.objects.get(
        environment=experiment.environment,
        feature=experiment.feature,
        feature_segment__segment=experiment.rollout_segment,
    )
    override_allocations = {
        mv.multivariate_feature_option_id: mv.percentage_allocation
        for mv in override.multivariate_feature_state_values.all()
    }
    assert override_allocations == {option_a.id: 60.0, option_b.id: 40.0}


def test_apply_experiment_rollout__existing_segment__leaves_default_allocations(
    experiment_with_rollout: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
) -> None:
    # Given
    experiment = experiment_with_rollout
    option_a, option_b, _ = multivariate_options
    default_state = FeatureState.objects.get(
        environment=experiment.environment,
        feature=experiment.feature,
        feature_segment__isnull=True,
        identity__isnull=True,
    )
    # A later manual edit to the default allocations must survive a rollout update.
    default_state.multivariate_feature_state_values.filter(
        multivariate_feature_option=option_a
    ).update(percentage_allocation=25.0)

    # When
    services.apply_experiment_rollout(
        experiment,
        RolloutSpec(
            enabled=True,
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

    # Then the manual edit to the default allocations survives...
    allocation = default_state.multivariate_feature_state_values.get(
        multivariate_feature_option=option_a
    ).percentage_allocation
    assert allocation == 25.0

    # ...while the rollout update itself is applied
    condition = Condition.objects.get(rule__segment=experiment.rollout_segment)
    assert condition.value == "80.0"
    override = FeatureState.objects.get(
        environment=experiment.environment,
        feature=experiment.feature,
        feature_segment__segment=experiment.rollout_segment,
    )
    override_allocations = {
        mv.multivariate_feature_option_id: mv.percentage_allocation
        for mv in override.multivariate_feature_state_values.all()
    }
    assert override_allocations == {option_a.id: 50.0, option_b.id: 50.0}


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
    segment = Segment.objects.get(pk=experiment.rollout_segment_id)
    assert segment.rules_data == [
        {
            "type": SegmentRule.ALL_RULE,
            "conditions": [
                {
                    "property": "$.identity.key",
                    "operator": PERCENTAGE_SPLIT,
                    "value": "80.0",
                    "description": None,
                }
            ],
            "rules": [],
        }
    ]
    # TODO: Drop the legacy rows as per https://github.com/Flagsmith/flagsmith/issues/7818
    assert _rules_from_orm(segment) == segment.rules_data

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


def _verification_count(result: str) -> float:
    return (
        REGISTRY.get_sample_value(
            "flagsmith_experimentation_warehouse_connection_verifications_total",
            {"result": result},
        )
        or 0.0
    )


def test_verify_clickhouse_connection__reachable__sets_connected(
    clickhouse_connection: WarehouseConnection,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given
    get_client = mocker.patch(
        "experimentation.warehouse_delivery_service.clickhouse_connect.get_client",
    )
    success_count_before = _verification_count("success")
    clickhouse_connection.status_detail = "stale detail"
    clickhouse_connection.save()

    # When
    verify_clickhouse_connection(clickhouse_connection)

    # Then the check ran over the same HTTP client delivery uses
    clickhouse_connection.refresh_from_db()
    assert clickhouse_connection.status == WarehouseConnectionStatus.CONNECTED
    assert clickhouse_connection.status_detail is None
    get_client.assert_called_once_with(
        host="ch.acme-corp.example",
        port=8443,
        username="acme_svc",
        password="hunter2",
        database="acme_dwh",
        secure=True,
        connect_timeout=10,
        send_receive_timeout=services.CLICKHOUSE_VERIFY_TIMEOUT_SECONDS,
        pool_mgr=mocker.ANY,
    )
    get_client.return_value.query.assert_called_once_with("EXISTS TABLE events")
    get_client.return_value.close.assert_called_once_with()
    assert _verification_count("success") == success_count_before + 1
    assert {
        "level": "info",
        "event": "connection.verification_succeeded",
        "environment__id": clickhouse_connection.environment_id,
        "organisation__id": (clickhouse_connection.environment.project.organisation_id),
    } in log.events


@pytest.mark.parametrize(
    "credentials, query_results, expected_detail",
    [
        (
            {"password": "hunter2"},
            Exception("connection refused"),
            "Connection failed.",
        ),
        (
            {"password": "hunter2"},
            [[(0,)]],
            "Events table not found in the configured database. "
            "Run the setup SQL to create it.",
        ),
        (None, None, "Stored connection details are incomplete."),
    ],
    ids=["client_error", "missing_events_table", "missing_credentials"],
)
def test_verify_clickhouse_connection__failure__sets_errored_with_detail(
    clickhouse_connection: WarehouseConnection,
    credentials: dict[str, str] | None,
    query_results: Exception | list[list[tuple[int]]] | None,
    expected_detail: str,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given
    get_client = mocker.patch(
        "experimentation.warehouse_delivery_service.clickhouse_connect.get_client",
    )
    if isinstance(query_results, list):
        get_client.return_value.query.side_effect = [
            mocker.Mock(result_rows=rows) for rows in query_results
        ]
    else:
        get_client.return_value.query.side_effect = query_results
    clickhouse_connection.credentials = credentials
    clickhouse_connection.save()
    failure_count_before = _verification_count("failure")

    # When
    verify_clickhouse_connection(clickhouse_connection)

    # Then
    clickhouse_connection.refresh_from_db()
    assert clickhouse_connection.status == WarehouseConnectionStatus.ERRORED
    assert clickhouse_connection.status_detail == expected_detail
    assert _verification_count("failure") == failure_count_before + 1
    assert any(
        event["event"] == "connection.verification_failed" for event in log.events
    )


def test_verify_clickhouse_connection__internal_host__sets_errored_without_connecting(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    get_client = mocker.patch(
        "experimentation.warehouse_delivery_service.clickhouse_connect.get_client",
    )
    clickhouse_connection.config = {
        **(clickhouse_connection.config or {}),
        "host": "10.0.0.5",
    }
    clickhouse_connection.save()

    # When
    verify_clickhouse_connection(clickhouse_connection)

    # Then
    clickhouse_connection.refresh_from_db()
    assert clickhouse_connection.status == WarehouseConnectionStatus.ERRORED
    assert (
        clickhouse_connection.status_detail
        == "Host must not target internal or private network addresses."
    )
    get_client.assert_not_called()


@pytest.mark.parametrize(
    "query_result, expected_stats",
    [
        (
            [(42, 7)],
            WarehouseEventStats(total_events_received=42, unique_events_count=7),
        ),
        (Exception("connection refused"), None),
    ],
    ids=["reachable", "unreachable"],
)
def test_annotate_warehouse_event_stats__clickhouse_connection__queries_customer_instance(
    clickhouse_connection: WarehouseConnection,
    reset_cache: None,
    query_result: Exception | list[tuple[int, int]],
    expected_stats: WarehouseEventStats | None,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given
    get_client = mocker.patch(
        "experimentation.warehouse_delivery_service.clickhouse_connect.get_client",
    )
    if isinstance(query_result, Exception):
        get_client.return_value.query.side_effect = query_result
    else:
        get_client.return_value.query.return_value = mocker.Mock(
            result_rows=query_result
        )

    # When
    annotate_warehouse_event_stats(clickhouse_connection, "test-env-key")

    # Then
    assert getattr(clickhouse_connection, "event_stats", None) == expected_stats
    get_client.return_value.query.assert_called_once_with(
        "SELECT count() AS total, uniqExact(event) AS unique "
        "FROM events WHERE environment_key = %(environment_key)s",
        parameters={"environment_key": "test-env-key"},
    )
    get_client.return_value.close.assert_called_once_with()
    assert any(
        event["event"] == "connection.event_stats_failed" for event in log.events
    ) == (expected_stats is None)

    # When — the outcome is cached, so a second request doesn't reconnect
    fresh_connection = WarehouseConnection.objects.get(id=clickhouse_connection.id)
    annotate_warehouse_event_stats(fresh_connection, "test-env-key")

    # Then
    get_client.assert_called_once()
    assert getattr(fresh_connection, "event_stats", None) == expected_stats


def test_get_experiment_flag_config__flag_disabled__returns_empty(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = MagicMock()
    mock_client.get_boolean_value.return_value = False
    mocker.patch(
        "experimentation.services.get_openfeature_client",
        return_value=mock_client,
    )

    # When
    result = services.get_experiment_flag_config(organisation)

    # Then
    assert result == {}
    mock_client.get_string_value.assert_not_called()


def test_get_experiment_flag_config__flag_enabled_with_valid_json__returns_parsed(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = MagicMock()
    mock_client.get_boolean_value.return_value = True
    mock_client.get_string_value.return_value = '{"auto_connect_warehouse": true}'
    mocker.patch(
        "experimentation.services.get_openfeature_client",
        return_value=mock_client,
    )

    # When
    result = services.get_experiment_flag_config(organisation)

    # Then
    assert result == {"auto_connect_warehouse": True}


@pytest.mark.parametrize(
    "raw_value",
    ["not-json", "", None],
    ids=["invalid-json", "empty-string", "none"],
)
def test_get_experiment_flag_config__flag_enabled_with_bad_value__returns_empty(
    organisation: Organisation,
    mocker: MockerFixture,
    raw_value: str | None,
) -> None:
    # Given
    mock_client = MagicMock()
    mock_client.get_boolean_value.return_value = True
    mock_client.get_string_value.return_value = raw_value
    mocker.patch(
        "experimentation.services.get_openfeature_client",
        return_value=mock_client,
    )

    # When
    result = services.get_experiment_flag_config(organisation)

    # Then
    assert result == {}


def test_get_experiment_flag_config__flag_enabled_with_non_dict_json__returns_empty(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = MagicMock()
    mock_client.get_boolean_value.return_value = True
    mock_client.get_string_value.return_value = '["free"]'
    mocker.patch(
        "experimentation.services.get_openfeature_client",
        return_value=mock_client,
    )

    # When
    result = services.get_experiment_flag_config(organisation)

    # Then
    assert result == {}


@pytest.mark.django_db()
def test_ensure_flagsmith_warehouse_connection__auto_connect_disabled__returns_none(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "experimentation.services.get_experiment_flag_config",
        return_value={},
    )

    # When
    result = services.ensure_flagsmith_warehouse_connection(environment)

    # Then
    assert result is None
    assert not WarehouseConnection.objects.filter(
        environment=environment,
    ).exists()


@pytest.mark.django_db()
def test_ensure_flagsmith_warehouse_connection__auto_connect_enabled__creates_connection(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "experimentation.services.get_experiment_flag_config",
        return_value={"auto_connect_warehouse": True},
    )

    # When
    result = services.ensure_flagsmith_warehouse_connection(environment)

    # Then
    assert result is not None
    assert result.warehouse_type == WarehouseType.FLAGSMITH
    assert result.name == "Flagsmith"
    assert result.environment == environment


@pytest.mark.django_db()
def test_ensure_flagsmith_warehouse_connection__connection_already_exists__returns_none(
    environment: Environment,
    warehouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "experimentation.services.get_experiment_flag_config",
        return_value={"auto_connect_warehouse": True},
    )

    # When
    result = services.ensure_flagsmith_warehouse_connection(environment)

    # Then
    assert result is None
    assert (
        WarehouseConnection.objects.filter(
            environment=environment,
            deleted_at__isnull=True,
        ).count()
        == 1
    )


def test_ensure_flagsmith_warehouse_connection__race_condition__handles_integrity_error(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "experimentation.services.get_experiment_flag_config",
        return_value={"auto_connect_warehouse": True},
    )
    mocker.patch.object(
        WarehouseConnection.objects,
        "filter",
        return_value=MagicMock(exists=MagicMock(return_value=False)),
    )
    mocker.patch.object(
        WarehouseConnection.objects,
        "create",
        side_effect=IntegrityError("duplicate"),
    )

    # When
    result = services.ensure_flagsmith_warehouse_connection(environment)

    # Then
    assert result is None


def _split_rule(rollout_percentage: str) -> dict[str, Any]:
    return {
        "type": SegmentRule.ALL_RULE,
        "conditions": [
            {
                "property": "$.identity.key",
                "operator": PERCENTAGE_SPLIT,
                "value": rollout_percentage,
                "description": None,
            }
        ],
        "rules": [],
    }


def _audience_rule(
    *segment_rules: list[dict[str, Any]],
    match: str = SegmentRule.ANY_RULE,
) -> dict[str, Any]:
    """A segment with a single top-level rule is inlined; a multi-rule segment
    is wrapped in an ALL rule, mirroring ``_compile_audience``."""
    return {
        "type": match,
        "conditions": [],
        "rules": [
            (
                rules[0]
                if len(rules) == 1
                else {"type": SegmentRule.ALL_RULE, "conditions": [], "rules": rules}
            )
            for rules in segment_rules
        ],
    }


def _condition_rule(property: str, value: str) -> list[dict[str, Any]]:
    return [
        {
            "type": SegmentRule.ALL_RULE,
            "conditions": [
                {
                    "property": property,
                    "operator": EQUAL,
                    "value": value,
                    "description": None,
                }
            ],
            "rules": [],
        }
    ]


def _snapshot_ids(experiment: Experiment) -> list[int]:
    """The segment ids recorded in the experiment's stored audience snapshot."""
    return [segment["id"] for segment in experiment.audience.get("segments", [])]


def _rules_from_orm(segment: Segment) -> list[dict[str, Any]]:
    """Read the segment's legacy rule rows back into the shape ``rules_data``
    holds, so the two representations can be compared."""

    def _rule(rule: SegmentRule) -> dict[str, Any]:
        return {
            "type": rule.type,
            "conditions": [
                {
                    "property": condition.property,
                    "operator": condition.operator,
                    "value": condition.value,
                    "description": condition.description,
                }
                for condition in rule.conditions.order_by("id")
            ],
            "rules": [_rule(sub_rule) for sub_rule in rule.rules.order_by("id")],
        }

    return [_rule(rule) for rule in segment.rules.order_by("id")]


def test_apply_experiment_rollout__audience_segment__compiles_rules_into_both_representations(
    experiment: Experiment,
    audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    nested_rule = SegmentRule.objects.create(
        rule=audience_segment.rules.get(), type=SegmentRule.ANY_RULE
    )
    Condition.objects.create(
        rule=nested_rule, property="plan", operator=EQUAL, value="pro"
    )
    second_top_rule = SegmentRule.objects.create(
        segment=audience_segment, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(
        rule=second_top_rule, property="device", operator=EQUAL, value="mobile"
    )

    # When
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            rollout_percentage=25.0,
            audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
        ),
    )

    # Then
    experiment.refresh_from_db()
    segment = experiment.rollout_segment
    assert segment is not None
    expected = [
        _split_rule("25.0"),
        _audience_rule(
            [
                {
                    "type": SegmentRule.ALL_RULE,
                    "conditions": [
                        {
                            "property": "country",
                            "operator": EQUAL,
                            "value": "uk",
                            "description": None,
                        }
                    ],
                    "rules": [
                        {
                            "type": SegmentRule.ANY_RULE,
                            "conditions": [
                                {
                                    "property": "plan",
                                    "operator": EQUAL,
                                    "value": "pro",
                                    "description": None,
                                }
                            ],
                            "rules": [],
                        }
                    ],
                },
                *_condition_rule("device", "mobile"),
            ]
        ),
    ]
    assert segment.rules_data == expected

    assert _rules_from_orm(segment) == expected

    assert experiment.audience["match"] == "any"
    assert experiment.audience["segments"] == [
        {
            "id": audience_segment.id,
            "uuid": str(audience_segment.uuid),
            "name": "UK users",
            "is_cohort": False,
            "cohort_source_type": None,
        }
    ]
    assert experiment.audience["taken_at"]
    assert experiment.audience["rules"] == segment.rules_data[1:]


@pytest.mark.parametrize(
    "use_new_segment, expected_extra_rules",
    [
        pytest.param(
            True,
            [
                _audience_rule(
                    _condition_rule("plan", "pro"), match=SegmentRule.ALL_RULE
                )
            ],
            id="replaced",
        ),
        pytest.param(False, [], id="removed"),
    ],
)
def test_apply_experiment_rollout__audience_changed_while_created__recompiles(
    use_new_segment: bool,
    expected_extra_rules: list[dict[str, Any]],
    experiment: Experiment,
    audience_segment: Segment,
    other_audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            enabled=False,
            audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
        ),
    )
    experiment.refresh_from_db()

    # When
    new_segment_ids = [other_audience_segment.id] if use_new_segment else []
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            enabled=False,
            audience=AudienceSpec(match="all", segment_ids=new_segment_ids),
        ),
    )

    # Then
    segment = Segment.objects.get(pk=experiment.rollout_segment_id)
    expected = [_split_rule("100.0"), *expected_extra_rules]
    assert segment.rules_data == expected
    assert _rules_from_orm(segment) == expected
    assert _snapshot_ids(experiment) == new_segment_ids
    assert experiment.audience["rules"] == expected_extra_rules


def test_apply_experiment_rollout__same_audience_while_created__recompiles_fresh_copy(
    experiment: Experiment,
    audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            enabled=False,
            audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
        ),
    )
    experiment.refresh_from_db()
    Condition.objects.filter(rule__segment=audience_segment).update(value="fr")

    # When
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            enabled=False,
            audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
        ),
    )

    # Then
    segment = Segment.objects.get(pk=experiment.rollout_segment_id)
    expected = [
        _split_rule("100.0"),
        _audience_rule(_condition_rule("country", "fr")),
    ]
    assert segment.rules_data == expected
    assert experiment.audience["rules"] == expected[1:]


def test_apply_experiment_rollout__empty_audience_match_toggled_while_created__stored(
    experiment: Experiment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(enabled=False, audience=AudienceSpec(match="any", segment_ids=[])),
    )
    experiment.refresh_from_db()
    assert experiment.audience["match"] == "any"

    # When
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(enabled=False, audience=AudienceSpec(match="all", segment_ids=[])),
    )

    # Then
    assert experiment.audience["match"] == "all"


def test_get_environment_document__nested_audience_rules__no_lazy_queries(
    experiment: Experiment,
    audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    api_key = experiment.environment.api_key
    audience = AudienceSpec(match="any", segment_ids=[audience_segment.id])
    services.apply_experiment_rollout(
        experiment, rollout_spec(enabled=False, audience=audience)
    )
    with CaptureQueriesContext(connection) as shallow_queries:
        Environment.get_environment_document(api_key)

    # When the copied audience gains a level of nested rules
    for index in range(3):
        nested_rule = SegmentRule.objects.create(
            rule=audience_segment.rules.get(), type=SegmentRule.ANY_RULE
        )
        Condition.objects.create(
            rule=nested_rule, property=f"prop{index}", operator=EQUAL, value="yes"
        )
    experiment.refresh_from_db()
    services.apply_experiment_rollout(
        experiment, rollout_spec(enabled=False, audience=audience)
    )

    # Then the extra level costs two prefetch queries (its conditions and its
    # empty sub-rules), not one query per nested rule
    with CaptureQueriesContext(connection) as nested_queries:
        Environment.get_environment_document(api_key)
    assert len(nested_queries) == len(shallow_queries) + 2


def test_apply_experiment_rollout__rules_unchanged__keeps_rule_rows(
    experiment: Experiment,
    audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
        ),
    )
    experiment.refresh_from_db()
    rollout_segment_id = experiment.rollout_segment_id
    assert rollout_segment_id is not None
    rule_ids = set(
        SegmentRule.objects.filter(segment_id=rollout_segment_id).values_list(
            "id", flat=True
        )
    )

    # When
    services.apply_experiment_rollout(
        experiment,
        replace(
            rollout_spec(
                audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
            ),
            feature_state_value="updated",
        ),
    )

    # Then
    assert (
        set(
            SegmentRule.objects.filter(segment_id=rollout_segment_id).values_list(
                "id", flat=True
            )
        )
        == rule_ids
    )


@pytest.mark.parametrize(
    "status",
    [ExperimentStatus.RUNNING, ExperimentStatus.PAUSED],
)
def test_apply_experiment_rollout__new_audience_while_running__raises(
    status: ExperimentStatus,
    experiment: Experiment,
    audience_segment: Segment,
    other_audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
        ),
    )
    experiment.refresh_from_db()
    Experiment.objects.filter(pk=experiment.pk).update(status=status)
    assert experiment.status == ExperimentStatus.CREATED

    # When / Then
    with pytest.raises(ValidationError, match="Cannot change the audience"):
        services.apply_experiment_rollout(
            experiment,
            rollout_spec(
                audience=AudienceSpec(
                    match="any",
                    segment_ids=[audience_segment.id, other_audience_segment.id],
                ),
            ),
        )
    assert Segment.objects.get(pk=experiment.rollout_segment_id).rules_data == [
        _split_rule("100.0"),
        _audience_rule(_condition_rule("country", "uk")),
    ]


def test_apply_experiment_rollout__audience__logs_rollout_applied_on_commit(  # type: ignore[no-untyped-def]
    experiment: Experiment,
    audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
    admin_user: FFAdminUser,
    log: StructuredLogCapture,
    django_capture_on_commit_callbacks,
) -> None:
    # Given / When
    with django_capture_on_commit_callbacks(execute=True):
        services.apply_experiment_rollout(
            experiment,
            rollout_spec(
                rollout_percentage=40.0,
                audience=AudienceSpec(match="all", segment_ids=[audience_segment.id]),
            ),
        )
        # Then
        assert not any(event["event"] == "rollout.applied" for event in log.events)

    # Then
    assert {
        "level": "info",
        "event": "rollout.applied",
        "experiment__id": experiment.id,
        "environment__id": experiment.environment_id,
        "feature__id": experiment.feature_id,
        "author__id": admin_user.pk,
        "rollout__percentage": 40.0,
        "audience__match": "all",
        "author__api_key_id": None,
        "audience__segments_count": 1,
        "audience__segment_ids": [audience_segment.id],
    } in log.events


@pytest.mark.parametrize(
    "change_source",
    [
        pytest.param(lambda segment: None, id="unchanged"),
        pytest.param(
            lambda segment: Condition.objects.filter(rule__segment=segment).update(
                value="fr"
            ),
            id="condition_edited",
        ),
        pytest.param(lambda segment: segment.delete(), id="deleted"),
        pytest.param(
            lambda segment: Condition.objects.create(
                rule=segment.rules.get(),
                property="$.identity.key",
                operator=PERCENTAGE_SPLIT,
                value="50",
            ),
            id="percentage_split_added",
        ),
    ],
)
def test_apply_experiment_rollout__same_audience_while_running__keeps_frozen_rules(
    change_source: Callable[[Segment], object],
    experiment: Experiment,
    audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            rollout_percentage=20.0,
            audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
        ),
    )
    experiment.refresh_from_db()
    experiment.status = ExperimentStatus.RUNNING
    experiment.save()
    change_source(audience_segment)

    # When
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            rollout_percentage=60.0,
            audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
        ),
    )

    # Then
    segment = Segment.objects.get(pk=experiment.rollout_segment_id)
    expected = [
        _split_rule("60.0"),
        _audience_rule(_condition_rule("country", "uk")),
    ]
    assert segment.rules_data == expected
    assert _rules_from_orm(segment) == expected
    rollout = services.get_experiment_rollout(experiment)
    assert rollout is not None
    assert rollout["rollout_percentage"] == 60.0


def _foreign_project_segment(project_b: Project, **_: Any) -> list[int]:
    segment = Segment.objects.create(project=project_b, name="Elsewhere")
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, property="a", operator=EQUAL, value="b")
    return [segment.id]


def _system_segment(project: Project, **_: Any) -> list[int]:
    segment = Segment.objects.create(
        project=project, name="System", is_system_segment=True
    )
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, property="a", operator=EQUAL, value="b")
    return [segment.id]


def _feature_specific_segment(
    project: Project, feature: Feature, **_: Any
) -> list[int]:
    segment = Segment.objects.create(
        project=project, name="Feature specific", feature=feature
    )
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, property="a", operator=EQUAL, value="b")
    return [segment.id]


def _other_environment_cohort_segment(project: Project, **_: Any) -> list[int]:
    other_environment = Environment.objects.create(
        name="Other environment", project=project
    )
    cohort = create_cohort(environment=other_environment, name="Elsewhere cohort")
    return [cohort.segment_id]


def _pending_deletion_cohort_segment(environment: Environment, **_: Any) -> list[int]:
    cohort = create_cohort(environment=environment, name="Draining cohort")
    cohort.deletion_requested_at = datetime.now(timezone.utc)
    cohort.save()
    return [cohort.segment_id]


def _percentage_split_segment(project: Project, **_: Any) -> list[int]:
    segment = Segment.objects.create(project=project, name="Half of everyone")
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    nested_rule = SegmentRule.objects.create(rule=rule, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=nested_rule,
        property="$.identity.key",
        operator=PERCENTAGE_SPLIT,
        value="50",
    )
    return [segment.id]


def _rule_less_segment(project: Project, **_: Any) -> list[int]:
    return [Segment.objects.create(project=project, name="No rules").id]


def _too_many_segments(project: Project, **_: Any) -> list[int]:
    segment_ids = []
    for index in range(MAX_AUDIENCE_SEGMENTS + 1):
        segment = Segment.objects.create(project=project, name=f"Segment {index}")
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(rule=rule, property="a", operator=EQUAL, value="b")
        segment_ids.append(segment.id)
    return segment_ids


def _duplicate_segments(project: Project, **_: Any) -> list[int]:
    segment_id = _system_segment(project)[0]
    return [segment_id, segment_id]


def _unknown_segment(**_: Any) -> list[int]:
    return [999999]


@pytest.mark.parametrize(
    "build_segment_ids, expected_error",
    [
        pytest.param(
            _foreign_project_segment,
            "do not belong to the project",
            id="foreign_project",
        ),
        pytest.param(_unknown_segment, "do not belong to the project", id="unknown"),
        pytest.param(_system_segment, "cannot be targeted", id="system"),
        pytest.param(
            _feature_specific_segment, "specific to a feature", id="feature_specific"
        ),
        pytest.param(
            _other_environment_cohort_segment,
            "cohort in another environment",
            id="other_environment_cohort",
        ),
        pytest.param(
            _pending_deletion_cohort_segment,
            "cohort that is being deleted",
            id="pending_deletion_cohort",
        ),
        pytest.param(
            _percentage_split_segment,
            "contains a percentage split",
            id="percentage_split",
        ),
        pytest.param(_rule_less_segment, "has no rules", id="no_rules"),
        pytest.param(
            _too_many_segments,
            f"no more than {MAX_AUDIENCE_SEGMENTS} segments",
            id="over_cap",
        ),
        pytest.param(_duplicate_segments, "must be unique", id="duplicates"),
    ],
)
def test_apply_experiment_rollout__ineligible_audience_segment__raises(
    build_segment_ids: Callable[..., list[int]],
    expected_error: str,
    experiment: Experiment,
    environment: Environment,
    project: Project,
    project_b: Project,
    feature: Feature,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    segment_ids = build_segment_ids(
        environment=environment, project=project, project_b=project_b, feature=feature
    )

    # When / Then
    with pytest.raises(ValidationError, match=expected_error):
        services.apply_experiment_rollout(
            experiment,
            rollout_spec(audience=AudienceSpec(match="any", segment_ids=segment_ids)),
        )
    experiment.refresh_from_db()
    assert experiment.rollout_segment_id is None


def _identity_flag_value(
    identity: Identity, feature: Feature
) -> tuple[Any, int | None]:
    """The value the identity is served for the feature, and the id of the
    feature segment it came from (``None`` for the environment default)."""
    (feature_state,) = [
        feature_state
        for feature_state in identity.get_all_feature_states()
        if feature_state.feature_id == feature.id
    ]
    return (
        feature_state.get_feature_state_value(identity=identity),
        (
            feature_state.feature_segment.segment_id
            if feature_state.feature_segment
            else None
        ),
    )


@pytest.fixture()
def experiment_with_audience_rollout(
    experiment: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    rollout_spec: RolloutSpecFactory,
) -> Callable[[str, list[int]], Experiment]:
    """Roll the experiment out to every identity in the given audience, serving
    them all the first variant."""
    option_a, _, _ = multivariate_options

    def _apply(match: str, segment_ids: list[int]) -> Experiment:
        services.apply_experiment_rollout(
            experiment,
            rollout_spec(
                rollout_percentage=100.0,
                multivariate_values=[MultivariateValueChangeSet(option_a.id, 100.0)],
                audience=AudienceSpec(match=match, segment_ids=segment_ids),
            ),
        )
        experiment.refresh_from_db()
        return experiment

    return _apply


@pytest.mark.parametrize(
    "match, traits, is_enrolled",
    [
        pytest.param("all", {"country": "uk", "plan": "pro"}, True, id="all_both"),
        pytest.param("all", {"country": "uk"}, False, id="all_one"),
        pytest.param("any", {"plan": "pro"}, True, id="any_one"),
        pytest.param("any", {"country": "de"}, False, id="any_neither"),
        pytest.param("any", {}, False, id="no_traits"),
    ],
)
def test_experiment_rollout__two_segment_audience__enrolment_follows_any_all_match(
    match: str,
    traits: dict[str, str],
    is_enrolled: bool,
    multi_segment_audiences: None,
    environment: Environment,
    multivariate_feature: Feature,
    multivariate_options: list[MultivariateFeatureOption],
    audience_segment: Segment,
    other_audience_segment: Segment,
    experiment_with_audience_rollout: Callable[[str, list[int]], Experiment],
) -> None:
    # Given
    option_a, _, _ = multivariate_options
    experiment = experiment_with_audience_rollout(
        match, [audience_segment.id, other_audience_segment.id]
    )
    identity = Identity.objects.create(
        identifier="test-identity", environment=environment
    )
    for trait_key, trait_value in traits.items():
        Trait.objects.create(
            identity=identity, trait_key=trait_key, string_value=trait_value
        )

    # When
    value, segment_id = _identity_flag_value(identity, multivariate_feature)

    # Then
    if is_enrolled:
        assert (value, segment_id) == (
            option_a.string_value,
            experiment.rollout_segment_id,
        )
    else:
        assert (value, segment_id) == ("control", None)


def test_experiment_rollout__cohort_audience__enrols_members_only(
    environment: Environment,
    multivariate_feature: Feature,
    experiment_with_audience_rollout: Callable[[str, list[int]], Experiment],
) -> None:
    # Given
    cohort = create_cohort(environment=environment, name="Beta users")
    CohortMembership.objects.create(cohort=cohort, identifier="member")
    apply_pending_memberships(cohort)
    member = Identity.objects.get(environment=environment, identifier="member")
    outsider = Identity.objects.create(environment=environment, identifier="outsider")

    # When
    experiment = experiment_with_audience_rollout("any", [cohort.segment_id])

    # Then
    assert _identity_flag_value(member, multivariate_feature)[1] == (
        experiment.rollout_segment_id
    )
    assert _identity_flag_value(outsider, multivariate_feature)[1] is None


def test_get_experiment_rollout__audience__returns_segment_details(
    multi_segment_audiences: None,
    experiment: Experiment,
    environment: Environment,
    audience_segment: Segment,
    other_audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    cohort = create_cohort(environment=environment, name="Beta users")
    cohort_segment = cohort.segment
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            audience=AudienceSpec(
                match="all",
                segment_ids=[
                    audience_segment.id,
                    other_audience_segment.id,
                    cohort_segment.id,
                ],
            ),
        ),
    )
    other_audience_segment.delete()
    cohort.delete()
    cohort_segment.delete()

    # When
    rollout = services.get_experiment_rollout(experiment)

    # Then
    assert rollout is not None
    assert rollout["audience"] == {
        "match": "all",
        "segments": [
            {
                "id": audience_segment.id,
                "name": "UK users",
                "is_cohort": False,
                "cohort_source_type": None,
                "deleted": False,
            },
            {
                "id": other_audience_segment.id,
                "name": "Pro plan",
                "is_cohort": False,
                "cohort_source_type": None,
                "deleted": True,
            },
            {
                "id": cohort_segment.id,
                "name": "Beta users",
                "is_cohort": True,
                "cohort_source_type": CohortSourceType.CSV,
                "deleted": True,
            },
        ],
    }


def test_get_experiment_rollout__no_audience__returns_empty_audience(
    experiment_with_rollout: Experiment,
) -> None:
    # Given / When
    rollout = services.get_experiment_rollout(experiment_with_rollout)

    # Then
    assert rollout is not None
    assert rollout["audience"] == {"match": "any", "segments": []}


@pytest.mark.parametrize(
    "with_audience", [True, False], ids=["audience", "no_audience"]
)
def test_apply_experiment_rollout__rollout_segment_edited__restored_from_snapshot(
    with_audience: bool,
    experiment: Experiment,
    audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    audience = (
        AudienceSpec(match="any", segment_ids=[audience_segment.id])
        if with_audience
        else None
    )
    services.apply_experiment_rollout(
        experiment, rollout_spec(rollout_percentage=20.0, audience=audience)
    )
    experiment.refresh_from_db()
    Segment.objects.filter(pk=experiment.rollout_segment_id).update(
        rules_data=[_split_rule("20.0"), _audience_rule(_condition_rule("hax", "yes"))]
    )

    # When
    services.apply_experiment_rollout(experiment, rollout_spec(rollout_percentage=60.0))

    # Then
    segment = Segment.objects.get(pk=experiment.rollout_segment_id)
    expected = [_split_rule("60.0")]
    if with_audience:
        expected.append(_audience_rule(_condition_rule("country", "uk")))
    assert segment.rules_data == expected
    assert _rules_from_orm(segment) == expected


def test_apply_experiment_rollout__snapshot_without_rules__falls_back_and_backfills(
    experiment: Experiment,
    audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            rollout_percentage=20.0,
            audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
        ),
    )
    experiment.refresh_from_db()
    legacy_snapshot = {
        key: value for key, value in experiment.audience.items() if key != "rules"
    }
    Experiment.objects.filter(pk=experiment.pk).update(audience=legacy_snapshot)
    experiment.refresh_from_db()
    assert "rules" not in experiment.audience

    # When
    services.apply_experiment_rollout(experiment, rollout_spec(rollout_percentage=60.0))

    # Then
    segment = Segment.objects.get(pk=experiment.rollout_segment_id)
    assert segment.rules_data == [
        _split_rule("60.0"),
        _audience_rule(_condition_rule("country", "uk")),
    ]
    experiment.refresh_from_db()
    assert experiment.audience["rules"] == [
        _audience_rule(_condition_rule("country", "uk"))
    ]


def test_apply_experiment_rollout__empty_audience_resubmitted_while_running__allowed(
    experiment: Experiment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    services.apply_experiment_rollout(experiment, rollout_spec(rollout_percentage=20.0))
    experiment.refresh_from_db()
    experiment.status = ExperimentStatus.RUNNING
    experiment.save()

    # When
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            rollout_percentage=60.0,
            audience=AudienceSpec(match="all", segment_ids=[]),
        ),
    )

    # Then
    segment = Segment.objects.get(pk=experiment.rollout_segment_id)
    assert segment.rules_data == [_split_rule("60.0")]


def test_apply_experiment_rollout__audience_change_while_enabled__raises(
    experiment: Experiment,
    audience_segment: Segment,
    other_audience_segment: Segment,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            enabled=True,
            audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
        ),
    )
    experiment.refresh_from_db()
    assert experiment.status == ExperimentStatus.CREATED

    # When / Then
    with pytest.raises(ValidationError, match="while the rollout is enabled"):
        services.apply_experiment_rollout(
            experiment,
            rollout_spec(
                enabled=True,
                audience=AudienceSpec(
                    match="any", segment_ids=[other_audience_segment.id]
                ),
            ),
        )
    assert _snapshot_ids(experiment) == [audience_segment.id]


def test_apply_experiment_rollout__any_audience__writes_audit_log(
    experiment: Experiment,
    audience_segment: Segment,
    admin_user: FFAdminUser,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given / When
    services.apply_experiment_rollout(
        experiment,
        rollout_spec(
            rollout_percentage=40.0,
            audience=AudienceSpec(match="all", segment_ids=[audience_segment.id]),
        ),
    )

    # Then
    audit_log = AuditLog.objects.get(
        related_object_type=RelatedObjectType.EXPERIMENT.name,
        related_object_id=experiment.id,
    )
    assert audit_log.log == (
        f"Experiment 'Test Experiment' rollout set to 40.0% of "
        f"segments [{audience_segment.id}] (all)"
    )
    assert audit_log.author_id == admin_user.pk
    assert audit_log.environment_id == experiment.environment_id


def test_apply_experiment_rollout__no_audience__names_all_identities_and_stores_empty_snapshot(
    experiment: Experiment,
    admin_user: FFAdminUser,
    rollout_spec: RolloutSpecFactory,
) -> None:
    # Given / When
    services.apply_experiment_rollout(experiment, rollout_spec(rollout_percentage=25.0))

    # Then
    audit_log = AuditLog.objects.get(
        related_object_type=RelatedObjectType.EXPERIMENT.name,
        related_object_id=experiment.id,
    )
    assert audit_log.log == (
        "Experiment 'Test Experiment' rollout set to 25.0% of all identities"
    )
    experiment.refresh_from_db()
    assert experiment.audience["match"] == "any"
    assert experiment.audience["segments"] == []
    assert experiment.audience["rules"] == []
    assert experiment.audience["taken_at"]


def test_apply_experiment_rollout__master_api_key_author__attributes_audit_log(
    experiment: Experiment,
    admin_master_api_key: tuple[MasterAPIKey, str],
    multivariate_options: list[MultivariateFeatureOption],
) -> None:
    # Given
    master_api_key, _ = admin_master_api_key

    # When
    services.apply_experiment_rollout(
        experiment,
        RolloutSpec(
            enabled=True,
            rollout_percentage=30.0,
            feature_state_value="control",
            value_type="string",
            multivariate_values=[],
            author=AuthorData(api_key=master_api_key),
        ),
    )

    # Then
    audit_log = AuditLog.objects.get(
        related_object_type=RelatedObjectType.EXPERIMENT.name,
        related_object_id=experiment.id,
    )
    assert audit_log.author_id is None
    assert audit_log.master_api_key_id == master_api_key.id


def test_apply_experiment_rollout__resubmitted__records_history_only_on_change(  # type: ignore[no-untyped-def]
    experiment: Experiment,
    audience_segment: Segment,
    multivariate_options: list[MultivariateFeatureOption],
    rollout_spec: RolloutSpecFactory,
    log: StructuredLogCapture,
    django_capture_on_commit_callbacks,
) -> None:
    # Given
    option_a, _, _ = multivariate_options

    def _spec() -> RolloutSpec:
        return rollout_spec(
            rollout_percentage=40.0,
            multivariate_values=[MultivariateValueChangeSet(option_a.id, 100.0)],
            audience=AudienceSpec(match="any", segment_ids=[audience_segment.id]),
        )

    def _audit_log_count() -> int:
        count: int = AuditLog.objects.filter(
            related_object_type=RelatedObjectType.EXPERIMENT.name,
            related_object_id=experiment.id,
        ).count()
        return count

    services.apply_experiment_rollout(experiment, _spec())
    experiment.refresh_from_db()
    assert _audit_log_count() == 1

    # When
    with django_capture_on_commit_callbacks(execute=True):
        services.apply_experiment_rollout(experiment, _spec())

    # Then
    assert _audit_log_count() == 1
    assert not any(event["event"] == "rollout.applied" for event in log.events)

    # When / Then
    services.apply_experiment_rollout(
        experiment, replace(_spec(), feature_state_value="updated")
    )
    assert _audit_log_count() == 2
