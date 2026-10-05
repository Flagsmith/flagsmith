from experimentation.models import WarehouseType
from experimentation.warehouses.base import Warehouse
from experimentation.warehouses.clickhouse import ClickHouseWarehouse
from experimentation.warehouses.flagsmith import FlagsmithWarehouse

WAREHOUSES: dict[str, Warehouse] = {
    WarehouseType.FLAGSMITH: FlagsmithWarehouse(),
    WarehouseType.CLICKHOUSE: ClickHouseWarehouse(),
}


def get_warehouse(warehouse_type: str) -> Warehouse:
    return WAREHOUSES[warehouse_type]
