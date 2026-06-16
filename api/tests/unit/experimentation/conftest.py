import pytest
from django.urls import reverse
from pytest_mock import MockerFixture

from environments.models import Environment
from experimentation import ingestion_sync_service
from experimentation.models import (
    Experiment,
    ExperimentStatus,
    Metric,
    WarehouseConnection,
    WarehouseType,
)
from features.models import Feature


@pytest.fixture(autouse=True)
def mock_ingestion_redis_client(mocker: MockerFixture) -> None:
    ingestion_sync_service._get_client.cache_clear()
    mocker.patch("experimentation.ingestion_sync_service.RedisCluster.from_url")


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


@pytest.fixture()
def metric(environment: Environment) -> Metric:
    metric: Metric = Metric.objects.create(
        environment=environment,
        name="Sessions per User",
        definition={"version": 1, "event": "session_started"},
    )
    return metric


@pytest.fixture()
def experiment(
    environment: Environment,
    multivariate_feature: Feature,
) -> Experiment:
    experiment: Experiment = Experiment.objects.create(
        environment=environment,
        feature=multivariate_feature,
        name="Test Experiment",
        hypothesis="Test hypothesis",
        status=ExperimentStatus.CREATED,
    )
    return experiment
