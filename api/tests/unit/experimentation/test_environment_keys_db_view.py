from datetime import datetime, timedelta

from django.db import connection
from django.utils import timezone

from environments.models import Environment, EnvironmentAPIKey
from experimentation.models import WarehouseConnection


def read_environment_key(sdk_key: str) -> list[tuple[str, bool, datetime | None]]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT client_api_key, uses_external_warehouse, expires_at "
            "FROM experimentation_environment_keys WHERE sdk_key = %s",
            [sdk_key],
        )
        rows: list[tuple[str, bool, datetime | None]] = cursor.fetchall()
        return rows


def test_environment_keys_db_view__client_key_with_flagsmith_warehouse__finds_it(
    environment: Environment,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given an environment sending events to Flagsmith's warehouse

    # When
    rows = read_environment_key(environment.api_key)

    # Then
    assert rows == [(environment.api_key, False, None)]


def test_environment_keys_db_view__server_key__finds_its_client_key_and_expiry(
    environment: Environment,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given
    expires_at = timezone.now() + timedelta(days=30)
    server_key = EnvironmentAPIKey.objects.create(
        environment=environment,
        name="Backend",
        expires_at=expires_at,
    )

    # When
    rows = read_environment_key(server_key.key)

    # Then
    assert rows == [(environment.api_key, False, expires_at)]


def test_environment_keys_db_view__client_key_with_external_warehouse__flags_external_warehouse(
    environment: Environment,
    clickhouse_connection: WarehouseConnection,
) -> None:
    # Given an environment sending events to the customer's ClickHouse

    # When
    rows = read_environment_key(environment.api_key)

    # Then
    assert rows == [(environment.api_key, True, None)]


def test_environment_keys_db_view__environment_without_connection__finds_nothing(
    environment: Environment,
) -> None:
    # Given an environment that has not set up experimentation

    # When
    rows = read_environment_key(environment.api_key)

    # Then
    assert rows == []


def test_environment_keys_db_view__deleted_connection__finds_nothing(
    environment: Environment,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given
    warehouse_connection.delete()

    # When
    rows = read_environment_key(environment.api_key)

    # Then
    assert rows == []


def test_environment_keys_db_view__deleted_environment__finds_nothing(
    environment: Environment,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given an environment marked deleted, with its connection left active
    Environment.objects.filter(id=environment.id).update(deleted_at=timezone.now())

    # When
    rows = read_environment_key(environment.api_key)

    # Then
    assert rows == []


def test_environment_keys_db_view__inactive_server_key__finds_nothing(
    environment: Environment,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given
    server_key = EnvironmentAPIKey.objects.create(
        environment=environment,
        name="Backend",
        active=False,
    )

    # When
    rows = read_environment_key(server_key.key)

    # Then
    assert rows == []
