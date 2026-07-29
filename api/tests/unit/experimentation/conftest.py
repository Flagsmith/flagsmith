import pytest
from django.urls import reverse
from pytest_mock import MockerFixture

from core.dataclasses import AuthorData
from environments.models import Environment
from experimentation import ingestion_sync_service
from experimentation.dataclasses import RolloutSpec
from experimentation.models import (
    Experiment,
    ExperimentStatus,
    Metric,
    WarehouseConnection,
    WarehouseType,
)
from experimentation.services import apply_experiment_rollout
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from features.versioning.dataclasses import MultivariateValueChangeSet
from users.models import FFAdminUser


@pytest.fixture(autouse=True)
def mock_ingestion_redis_client(mocker: MockerFixture) -> None:
    ingestion_sync_service._get_client.cache_clear()
    mocker.patch("experimentation.ingestion_sync_service.RedisCluster.from_url")


@pytest.fixture(autouse=True)
def mock_provision_external_warehouse_ingestion_infrastructure(
    mocker: MockerFixture,
) -> None:
    # Creating an external warehouse connection enqueues provisioning, which
    # runs synchronously under test; stub it so tests don't reach AWS.
    mocker.patch(
        "experimentation.tasks.provision_external_warehouse_ingestion_infrastructure",
    )


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


@pytest.fixture()
def experiment_with_rollout(
    experiment: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
) -> Experiment:
    option_a, option_b, _ = multivariate_options
    apply_experiment_rollout(
        experiment,
        RolloutSpec(
            enabled=True,
            rollout_percentage=20.0,
            feature_state_value="control",
            value_type="string",
            multivariate_values=[
                MultivariateValueChangeSet(option_a.id, 50.0),
                MultivariateValueChangeSet(option_b.id, 50.0),
            ],
            author=AuthorData(user=admin_user),
        ),
    )
    return experiment


@pytest.fixture()
def clickhouse_connection(
    environment: Environment,
) -> WarehouseConnection:
    connection: WarehouseConnection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.CLICKHOUSE,
        name="Production ClickHouse",
        config={
            "host": "ch.acme-corp.example",
            "port": 9440,
            "database": "acme_dwh",
            "username": "acme_svc",
            "secure": True,
        },
        credentials={"password": "hunter2"},
    )
    return connection
