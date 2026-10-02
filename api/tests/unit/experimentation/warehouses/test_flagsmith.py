from collections.abc import Callable

import pytest
from rest_framework.exceptions import ValidationError

from experimentation.models import WarehouseConnection, WarehouseType
from experimentation.warehouses.base import UnsupportedWarehouseOperation
from experimentation.warehouses.flagsmith import FlagsmithWarehouse


def test_validate_config__empty__accepts() -> None:
    # Given
    warehouse = FlagsmithWarehouse()

    # When / Then
    warehouse.validate_config({})


def test_validate_config__any_setting__raises_validation_error() -> None:
    # Given
    warehouse = FlagsmithWarehouse()

    # When / Then
    with pytest.raises(ValidationError):
        warehouse.validate_config({"host": "x"})


@pytest.mark.parametrize(
    "operation",
    [
        lambda warehouse, connection: warehouse.validate_credentials({"token": "x"}),
        lambda warehouse, connection: warehouse.verify(connection),
        lambda warehouse, connection: warehouse.describe_error(Exception()),
        lambda warehouse, connection: warehouse.get_event_names(connection, "key"),
        lambda warehouse, connection: warehouse.get_event_stats(connection, "key"),
    ],
    ids=[
        "validate_credentials",
        "verify",
        "describe_error",
        "event_names",
        "event_stats",
    ],
)
def test_flagsmith_warehouse__operation_beyond_configuration__raises_unsupported(
    operation: Callable[[FlagsmithWarehouse, WarehouseConnection], object],
) -> None:
    # Given
    connection = WarehouseConnection(warehouse_type=WarehouseType.FLAGSMITH)

    # When / Then
    with pytest.raises(UnsupportedWarehouseOperation):
        operation(FlagsmithWarehouse(), connection)
