from datetime import datetime, timezone

import pytest

from environments.models import Environment
from experimentation.dataclasses import WarehouseEventStats
from experimentation.models import (
    WarehouseConnection,
    WarehouseConnectionStatus,
    WarehouseType,
)
from experimentation.serializers import WarehouseConnectionSerializer

pytestmark = pytest.mark.django_db


def test_create__no_existing__creates_new_connection(
    environment: Environment,
) -> None:
    # Given
    serializer = WarehouseConnectionSerializer(
        data={"warehouse_type": "flagsmith"},
    )
    serializer.is_valid(raise_exception=True)

    # When
    connection = serializer.save(environment=environment)

    # Then
    assert connection.pk is not None
    assert connection.warehouse_type == WarehouseType.FLAGSMITH
    assert connection.status == WarehouseConnectionStatus.CREATED
    assert connection.name == f"Flagsmith Warehouse - {environment.name}"


def test_create__soft_deleted_exists__creates_new_record(
    environment: Environment,
) -> None:
    # Given
    original = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Old Name",
    )
    original_pk = original.pk
    original.delete()

    serializer = WarehouseConnectionSerializer(
        data={"warehouse_type": "flagsmith"},
    )
    serializer.is_valid(raise_exception=True)

    # When
    connection = serializer.save(environment=environment)

    # Then
    assert connection.pk != original_pk
    assert connection.deleted_at is None
    assert connection.status == WarehouseConnectionStatus.CREATED
    assert connection.name == f"Flagsmith Warehouse - {environment.name}"


@pytest.mark.parametrize(
    "environment_name, expected_name",
    [
        ("Production", "Flagsmith Warehouse - Production"),
        ("e" * 300, f"Flagsmith Warehouse - {'e' * 233}"),
    ],
    ids=["short", "truncated-to-max-length"],
)
def test_create__environment_name__name_uses_warehouse_type_label(
    environment: Environment,
    environment_name: str,
    expected_name: str,
) -> None:
    # Given
    environment.name = environment_name
    serializer = WarehouseConnectionSerializer(
        data={"warehouse_type": "flagsmith"},
    )
    serializer.is_valid(raise_exception=True)

    # When
    connection = serializer.save(environment=environment)

    # Then
    assert connection.name == expected_name


def test_create__snowflake_minimal_config__applies_defaults(
    environment: Environment,
    snowflake_private_key_pem: str,
) -> None:
    # Given
    serializer = WarehouseConnectionSerializer(
        data={
            "warehouse_type": "snowflake",
            "name": "My Snowflake",
            "config": {"account_identifier": "acme-prod"},
            "credentials": {"private_key": snowflake_private_key_pem},
        },
    )
    serializer.is_valid(raise_exception=True)

    # When
    connection = serializer.save(environment=environment)

    # Then
    assert connection.config == {
        "account_identifier": "ACME-PROD",
        "warehouse": "FLAGSMITH_WH",
        "database": "FLAGSMITH",
        "schema": "FLAGSMITH_EXP",
        "role": "FLAGSMITH_ROLE",
        "user": "FLAGSMITH_SERVICE",
    }
    assert connection.credentials == {"private_key": snowflake_private_key_pem.strip()}


@pytest.mark.parametrize(
    "with_private_key, expected_errors",
    [
        (False, {"credentials": {"private_key": "This field is required."}}),
        (True, {"config": {"account_identifier": "This field is required."}}),
    ],
    ids=["missing-private-key", "missing-account-identifier"],
)
def test_create__snowflake_incomplete__raises_validation_error(
    environment: Environment,
    snowflake_private_key_pem: str,
    with_private_key: bool,
    expected_errors: dict[str, object],
) -> None:
    # Given
    serializer = WarehouseConnectionSerializer(
        data={
            "warehouse_type": "snowflake",
            "name": "Bad Snowflake",
            "config": {"warehouse": "MY_WH"},
            "credentials": (
                {"private_key": snowflake_private_key_pem} if with_private_key else {}
            ),
        },
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert serializer.errors == expected_errors


def test_create__flagsmith_with_config__raises_validation_error(
    environment: Environment,
) -> None:
    # Given
    serializer = WarehouseConnectionSerializer(
        data={
            "warehouse_type": "flagsmith",
            "config": {"account_identifier": "nope"},
        },
    )

    # When / Then
    assert not serializer.is_valid()
    assert "config" in serializer.errors


def test_warehouse_serializer__event_stats_attached__serializes_counts() -> None:
    # Given
    connection = WarehouseConnection(
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
        status=WarehouseConnectionStatus.CONNECTED,
    )
    connection.event_stats = WarehouseEventStats(
        total_events_received=7,
        unique_events_count=2,
        last_event_at=datetime(2026, 10, 12, 13, 23, 52, tzinfo=timezone.utc),
    )

    # When
    data = WarehouseConnectionSerializer(connection).data

    # Then
    assert data["total_events_received"] == 7
    assert data["unique_events_count"] == 2
    assert data["last_event_received_at"] == datetime(
        2026, 10, 12, 13, 23, 52, tzinfo=timezone.utc
    )


def test_create__flagsmith_with_credentials__raises_type_neutral_error() -> None:
    # Given
    serializer = WarehouseConnectionSerializer(
        data={"warehouse_type": "flagsmith", "credentials": {"password": "x"}},
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert serializer.errors == {
        "credentials": ["This warehouse type does not accept credentials."]
    }
