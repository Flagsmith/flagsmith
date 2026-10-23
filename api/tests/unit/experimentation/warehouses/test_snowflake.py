from collections.abc import Callable
from datetime import datetime, timezone

import pytest

from experimentation.models import WarehouseConnection, WarehouseType
from experimentation.warehouses.exceptions import UnsupportedWarehouseOperation
from experimentation.warehouses.snowflake import SnowflakeWarehouse

WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 8, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "operation",
    [
        lambda warehouse, connection: warehouse.validate_credentials({"token": "x"}),
        lambda warehouse, connection: warehouse.verify(connection),
        lambda warehouse, connection: warehouse.describe_error(Exception()),
        lambda warehouse, connection: warehouse.get_event_names(connection, "key"),
        lambda warehouse, connection: warehouse.get_event_stats(connection, "key"),
        lambda warehouse, connection: warehouse.get_exposure_buckets(
            connection,
            environment_key="key",
            feature_name="checkout",
            window_start=WINDOW_START,
            window_end=WINDOW_END,
            granularity="day",
        ),
        lambda warehouse, connection: warehouse.get_results_aggregates(
            connection,
            environment_key="key",
            feature_name="checkout",
            window_start=WINDOW_START,
            window_end=WINDOW_END,
            specs=[],
            granularity="day",
        ),
    ],
    ids=[
        "validate_credentials",
        "verify",
        "describe_error",
        "event_names",
        "event_stats",
        "exposure_buckets",
        "results_aggregates",
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
