import pytest

from experimentation.models import WarehouseType
from experimentation.warehouses.clickhouse import ClickHouseWarehouse
from experimentation.warehouses.flagsmith import FlagsmithWarehouse
from experimentation.warehouses.registry import WAREHOUSES, get_warehouse
from experimentation.warehouses.snowflake import SnowflakeWarehouse


def test_warehouses__every_warehouse_type__has_a_provider() -> None:
    # Given
    expected_types = set(WarehouseType)

    # When
    registered_types = set(WAREHOUSES)

    # Then
    assert registered_types == expected_types


@pytest.mark.parametrize(
    "warehouse_type, expected_class",
    [
        (WarehouseType.FLAGSMITH, FlagsmithWarehouse),
        (WarehouseType.CLICKHOUSE, ClickHouseWarehouse),
        (WarehouseType.SNOWFLAKE, SnowflakeWarehouse),
    ],
)
def test_get_warehouse__registered_type__returns_provider(
    warehouse_type: str,
    expected_class: type,
) -> None:
    # Given a registered warehouse type

    # When
    warehouse = get_warehouse(warehouse_type)

    # Then
    assert isinstance(warehouse, expected_class)


def test_get_warehouse__unregistered_type__raises_key_error() -> None:
    # Given
    warehouse_type = "bigquery"

    # When / Then
    with pytest.raises(KeyError):
        get_warehouse(warehouse_type)
