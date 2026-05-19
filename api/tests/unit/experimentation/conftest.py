import pytest

from environments.models import Environment
from experimentation.models import WarehouseConnection, WarehouseType


@pytest.fixture()
def warehouse_connection(environment: Environment) -> WarehouseConnection:
    return WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name=f"Flagsmith Warehouse - {environment.name}",
    )


@pytest.fixture()
def warehouse_connection_url(environment: Environment) -> str:
    return reverse_warehouse_connection_url(environment.api_key)


def reverse_warehouse_connection_url(environment_api_key: str) -> str:
    from django.urls import reverse

    return reverse(
        "api-v1:environments:experimentation:warehouse-connections",
        args=[environment_api_key],
    )
