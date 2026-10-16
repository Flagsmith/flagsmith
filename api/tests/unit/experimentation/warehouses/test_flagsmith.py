from collections.abc import Callable
from datetime import datetime, timezone

import pytest
from pytest_mock import MockerFixture
from rest_framework.exceptions import ValidationError

from experimentation.models import WarehouseConnection, WarehouseType
from experimentation.warehouses import flagsmith
from experimentation.warehouses.exceptions import UnsupportedWarehouseOperation
from experimentation.warehouses.flagsmith import FlagsmithWarehouse

WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 8, tzinfo=timezone.utc)


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
    ],
    ids=[
        "validate_credentials",
        "verify",
        "describe_error",
    ],
)
def test_flagsmith_warehouse__connection_management__raises_unsupported(
    operation: Callable[[FlagsmithWarehouse, WarehouseConnection], object],
) -> None:
    # Given
    connection = WarehouseConnection(warehouse_type=WarehouseType.FLAGSMITH)

    # When / Then
    with pytest.raises(UnsupportedWarehouseOperation):
        operation(FlagsmithWarehouse(), connection)


def test_get_exposure_buckets__window__reads_managed_warehouse(
    mocker: MockerFixture,
) -> None:
    # Given
    read = mocker.patch.object(flagsmith, "get_exposure_buckets")
    connection = WarehouseConnection(warehouse_type=WarehouseType.FLAGSMITH)

    # When
    buckets = FlagsmithWarehouse().get_exposure_buckets(
        connection,
        environment_key="key",
        feature_name="checkout",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        granularity="day",
    )

    # Then
    assert buckets is read.return_value
    read.assert_called_once_with(
        environment_key="key",
        feature_name="checkout",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        granularity="day",
    )


def test_get_results_aggregates__window__reads_managed_warehouse(
    mocker: MockerFixture,
) -> None:
    # Given
    read = mocker.patch.object(flagsmith, "get_results_aggregates")
    connection = WarehouseConnection(warehouse_type=WarehouseType.FLAGSMITH)

    # When
    aggregates = FlagsmithWarehouse().get_results_aggregates(
        connection,
        environment_key="key",
        feature_name="checkout",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        specs=[],
        granularity="day",
    )

    # Then
    assert aggregates is read.return_value
    read.assert_called_once_with(
        environment_key="key",
        feature_name="checkout",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        specs=[],
        granularity="day",
    )
