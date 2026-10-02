from collections.abc import Callable

import pytest

from experimentation.models import WarehouseConnection, WarehouseType
from experimentation.warehouses.base import UnsupportedWarehouseOperation
from experimentation.warehouses.snowflake import SnowflakeWarehouse


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
def test_snowflake_warehouse__operation_beyond_configuration__raises_unsupported(
    operation: Callable[[SnowflakeWarehouse, WarehouseConnection], object],
) -> None:
    # Given
    connection = WarehouseConnection(
        warehouse_type=WarehouseType.SNOWFLAKE,
        config={"account_identifier": "acme"},
    )

    # When / Then
    with pytest.raises(UnsupportedWarehouseOperation):
        operation(SnowflakeWarehouse(), connection)
