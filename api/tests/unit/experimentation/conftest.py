import pytest
from django.urls import reverse
from pytest_mock import MockerFixture

from environments.models import Environment
from experimentation.models import WarehouseConnection, WarehouseType


@pytest.fixture(autouse=True)
def mock_ingestion_redis_client(mocker: MockerFixture) -> None:
    mocker.patch("experimentation.ingestion_sync_service._get_client")


@pytest.fixture()
def warehouse_connection(environment: Environment) -> WarehouseConnection:
    connection: WarehouseConnection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name=f"Flagsmith Warehouse - {environment.name}",
    )
    return connection


@pytest.fixture()
def warehouse_connection_url(environment: Environment) -> str:
    return reverse(
        "api-v1:environments:experimentation:warehouse-connections-list",
        args=[environment.api_key],
    )
