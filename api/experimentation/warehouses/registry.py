from experimentation.models import WarehouseType
from experimentation.warehouses.base import Warehouse
from experimentation.warehouses.clickhouse import ClickHouseWarehouse
from experimentation.warehouses.databricks import DatabricksWarehouse
from experimentation.warehouses.flagsmith import FlagsmithWarehouse
from experimentation.warehouses.snowflake import SnowflakeWarehouse

WAREHOUSES: dict[str, Warehouse] = {
    WarehouseType.FLAGSMITH: FlagsmithWarehouse(),
    WarehouseType.CLICKHOUSE: ClickHouseWarehouse(),
    WarehouseType.SNOWFLAKE: SnowflakeWarehouse(),
    WarehouseType.DATABRICKS: DatabricksWarehouse(),
}


def get_warehouse(warehouse_type: str) -> Warehouse:
    return WAREHOUSES[warehouse_type]
