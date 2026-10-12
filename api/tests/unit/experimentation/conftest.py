from typing import Protocol

import pytest
from django.urls import reverse
from django.utils import timezone
from flag_engine.segments.constants import EQUAL
from pytest_mock import MockerFixture

from core.dataclasses import AuthorData
from environments.models import Environment
from experimentation.dataclasses import AudienceSpec, RolloutSpec
from experimentation.models import (
    Experiment,
    ExperimentStatus,
    Metric,
    WarehouseConnection,
    WarehouseConnectionStatus,
    WarehouseDeliveryStatus,
    WarehouseType,
)
from experimentation.services import apply_experiment_rollout
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from features.versioning.dataclasses import MultivariateValueChangeSet
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from users.models import FFAdminUser


class RolloutSpecFactory(Protocol):
    def __call__(
        self,
        *,
        rollout_percentage: float = ...,
        enabled: bool = ...,
        multivariate_values: list[MultivariateValueChangeSet] | None = ...,
        audience: AudienceSpec | None = ...,
    ) -> RolloutSpec: ...


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
            "port": 8443,
            "database": "acme_dwh",
            "username": "acme_svc",
            "secure": True,
        },
        credentials={"password": "hunter2"},
    )
    return connection


@pytest.fixture()
def databricks_connection() -> WarehouseConnection:
    connection = WarehouseConnection(
        warehouse_type="databricks",
        config={
            "host": "acme.cloud.databricks.com",
            "workspace_id": "1234567890",
            "region": "us-east-1",
            "warehouse_id": "abc123",
            "catalog": "main",
            "schema": "flagsmith_exp",
        },
    )
    connection.credentials = {"client_id": "sp-id", "client_secret": "sp-secret"}
    return connection


@pytest.fixture()
def failing_delivery_status(
    clickhouse_connection: WarehouseConnection,
) -> WarehouseDeliveryStatus:
    status: WarehouseDeliveryStatus = WarehouseDeliveryStatus.objects.create(
        connection=clickhouse_connection,
        status=WarehouseConnectionStatus.ERRORED,
        detail="Authentication failed.",
        updated_at=timezone.now(),
    )
    return status


@pytest.fixture()
def successful_delivery_status(
    clickhouse_connection: WarehouseConnection,
) -> WarehouseDeliveryStatus:
    status: WarehouseDeliveryStatus = WarehouseDeliveryStatus.objects.create(
        connection=clickhouse_connection,
        status=WarehouseConnectionStatus.CONNECTED,
        updated_at=timezone.now(),
    )
    return status


@pytest.fixture()
def rollout_spec(admin_user: FFAdminUser) -> RolloutSpecFactory:
    def _make(
        *,
        rollout_percentage: float = 100.0,
        enabled: bool = True,
        multivariate_values: list[MultivariateValueChangeSet] | None = None,
        audience: AudienceSpec | None = None,
    ) -> RolloutSpec:
        return RolloutSpec(
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            feature_state_value="control",
            value_type="string",
            multivariate_values=multivariate_values or [],
            author=AuthorData(user=admin_user),
            audience=audience,
        )

    return _make


@pytest.fixture()
def audience_segment(project: Project) -> Segment:
    """A segment matching identities with a ``country`` trait of ``uk``."""
    return _build_segment(project, name="UK users", property="country", value="uk")


@pytest.fixture()
def other_audience_segment(project: Project) -> Segment:
    """A segment matching identities with a ``plan`` trait of ``pro``."""
    return _build_segment(project, name="Pro plan", property="plan", value="pro")


@pytest.fixture()
def multi_segment_audiences(mocker: MockerFixture) -> None:
    """Lift the audience cap, so the multi-segment compilation the service
    already supports stays covered while the cap is held at one."""
    mocker.patch("experimentation.services.MAX_AUDIENCE_SEGMENTS", 5)


def _build_segment(
    project: Project,
    *,
    name: str,
    property: str,
    value: str,
) -> Segment:
    segment: Segment = Segment.objects.create(project=project, name=name)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, property=property, operator=EQUAL, value=value)
    return segment
