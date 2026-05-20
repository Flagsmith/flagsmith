import pytest

from environments.models import Environment
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
    assert connection.status == WarehouseConnectionStatus.PENDING_CONNECTION
    assert connection.name == f"Flagsmith Warehouse - {environment.name}"


def test_create__soft_deleted_exists__resurrects_record(
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
    assert connection.pk == original_pk
    assert connection.deleted_at is None
    assert connection.status == WarehouseConnectionStatus.PENDING_CONNECTION
    assert connection.name == f"Flagsmith Warehouse - {environment.name}"


def test_create__valid_data__name_uses_warehouse_type_label(
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
    assert connection.name.startswith("Flagsmith Warehouse")
    assert environment.name in connection.name
