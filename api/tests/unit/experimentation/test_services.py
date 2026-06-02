import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.models import Environment
from experimentation import services
from experimentation.dataclasses import WarehouseEventStats
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
