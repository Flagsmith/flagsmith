import json

from django.db import connection
from django.utils import timezone

from environments.models import Environment
from experimentation.models import WarehouseConnection
from experimentation.warehouse_credentials import decrypt_warehouse_credentials


def read_delivery_connection(client_api_key: str) -> list[tuple[object, ...]]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT connection_id, warehouse_type, config, credentials "
            "FROM experimentation_delivery_connections WHERE client_api_key = %s",
            [client_api_key],
        )
        rows: list[tuple[object, ...]] = cursor.fetchall()
        return rows


def test_delivery_connections_db_view__external_warehouse__finds_its_config_and_encrypted_credentials(
    environment: Environment,
    clickhouse_connection: WarehouseConnection,
) -> None:
    # Given an environment sending events to the customer's ClickHouse

    # When
    [(connection_id, warehouse_type, config, credentials)] = read_delivery_connection(
        environment.api_key
    )

    # Then
    assert (connection_id, warehouse_type, json.loads(str(config))) == (
        clickhouse_connection.id,
        "clickhouse",
        clickhouse_connection.config,
    )
    assert decrypt_warehouse_credentials(str(credentials)) == {"password": "hunter2"}


def test_delivery_connections_db_view__flagsmith_warehouse__finds_nothing(
    environment: Environment,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given an environment sending events to Flagsmith's warehouse

    # When
    rows = read_delivery_connection(environment.api_key)

    # Then
    assert rows == []


def test_delivery_connections_db_view__deleted_connection__finds_nothing(
    environment: Environment,
    clickhouse_connection: WarehouseConnection,
) -> None:
    # Given
    clickhouse_connection.delete()

    # When
    rows = read_delivery_connection(environment.api_key)

    # Then
    assert rows == []


def test_delivery_connections_db_view__deleted_environment__finds_nothing(
    environment: Environment,
    clickhouse_connection: WarehouseConnection,
) -> None:
    # Given an environment marked deleted, with its connection left active
    Environment.objects.filter(id=environment.id).update(deleted_at=timezone.now())

    # When
    rows = read_delivery_connection(environment.api_key)

    # Then
    assert rows == []
