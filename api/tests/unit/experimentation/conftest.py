import json
import uuid
from collections.abc import Iterator
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import openfeature.api as openfeature_api
import psycopg2
import pytest
from django.db import connection as django_connection
from django.urls import reverse
from django.utils import timezone
from flag_engine.segments.constants import EQUAL
from openfeature.provider.in_memory_provider import InMemoryFlag, InMemoryProvider
from psycopg2 import sql
from psycopg2.extensions import cursor as PgCursor
from pytest_mock import MockerFixture

from core.dataclasses import AuthorData
from environments.models import Environment
from experimentation.constants import WAREHOUSES_FLAG
from experimentation.dataclasses import (
    AudienceSpec,
    RolloutSpec,
)
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
from experimentation.warehouses.constants import FLAGSMITH_DATABASE_SOURCE
from experimentation.warehouses.postgres import flagsmith_database_connect_params
from features.future.types import Variant
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from integrations.flagsmith.client import DEFAULT_OPENFEATURE_DOMAIN
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from users.models import FFAdminUser


class RolloutSpecFactory(Protocol):
    def __call__(
        self,
        *,
        rollout_percentage: float = ...,
        enabled: bool = ...,
        variants: list[Variant] | None = ...,
        audience: AudienceSpec | None = ...,
    ) -> RolloutSpec: ...


class SetWarehousesFlagFixture(Protocol):
    def __call__(self, value: dict[str, object] | str) -> None: ...


@pytest.fixture()
def set_warehouses_flag() -> SetWarehousesFlagFixture:
    def _set_warehouses_flag(value: dict[str, object] | str) -> None:
        raw = value if isinstance(value, str) else json.dumps(value)
        flag = InMemoryFlag(variants={"value": raw}, default_variant="value")
        openfeature_api.set_provider(
            InMemoryProvider({WAREHOUSES_FLAG: flag}),
            domain=DEFAULT_OPENFEATURE_DOMAIN,
        )

    return _set_warehouses_flag


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
    option_a, option_b, option_c = multivariate_options
    apply_experiment_rollout(
        experiment,
        RolloutSpec(
            enabled=True,
            rollout_percentage=20.0,
            feature_state_value="control",
            value_type="string",
            variants=[
                {"id": option_a.id, "weight": 50.0},
                {"id": option_b.id, "weight": 50.0},
                {"id": option_c.id, "weight": 0.0},
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
def databricks_connection(
    environment: Environment,
) -> WarehouseConnection:
    connection: WarehouseConnection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.DATABRICKS,
        name="Production Databricks",
        config={
            "host": "acme.cloud.databricks.com",
            "workspace_id": "1234567890",
            "region": "us-east-1",
            "warehouse_id": "abc123",
            "catalog": "main",
            "schema": "flagsmith_exp",
        },
        credentials={"client_id": "sp-id", "client_secret": "sp-secret"},
    )
    return connection


POSTGRES_EVENTS_SQL_PATH = (
    Path(__file__).resolve().parents[4] / "experimentation" / "postgres" / "events.sql"
)


@dataclass
class PostgresWarehouseSchema:
    """An events table in its own schema, managed over a separate autocommit
    session so the provider's own connections see it."""

    cursor: PgCursor
    schema: str
    config: dict[str, object]
    password: str


@pytest.fixture()
def postgres_warehouse_schema(db: None) -> Iterator[PostgresWarehouseSchema]:
    settings = django_connection.settings_dict
    schema = f"exp_{uuid.uuid4().hex[:12]}"
    with closing(
        psycopg2.connect(
            host=settings["HOST"],
            port=settings["PORT"],
            dbname=settings["NAME"],
            user=settings["USER"],
            password=settings["PASSWORD"],
        )
    ) as admin:
        admin.autocommit = True
        with admin.cursor() as cursor:
            cursor.execute(
                POSTGRES_EVENTS_SQL_PATH.read_text().replace("flagsmith_exp", schema)
            )
            yield PostgresWarehouseSchema(
                cursor=cursor,
                schema=schema,
                config={
                    "host": settings["HOST"],
                    "port": int(settings["PORT"]),
                    "database": settings["NAME"],
                    "schema": schema,
                    "username": settings["USER"],
                    "sslmode": "disable",
                },
                password=settings["PASSWORD"],
            )
            cursor.execute(
                sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema))
            )


@pytest.fixture()
def postgres_connection(
    environment: Environment,
    postgres_warehouse_schema: PostgresWarehouseSchema,
) -> WarehouseConnection:
    connection: WarehouseConnection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.POSTGRES,
        name="Production PostgreSQL",
        config=postgres_warehouse_schema.config,
        credentials={"password": postgres_warehouse_schema.password},
    )
    return connection


@pytest.fixture()
def flagsmith_database_events_cursor(db: None) -> Iterator[PgCursor]:
    """An autocommit session on the Flagsmith database's events table, which
    migrations create; emptied on teardown."""
    with closing(psycopg2.connect(**flagsmith_database_connect_params())) as admin:
        admin.autocommit = True
        with admin.cursor() as cursor:
            yield cursor
            cursor.execute("TRUNCATE flagsmith_exp.events")


@pytest.fixture()
def flagsmith_database_connection(
    environment: Environment,
) -> WarehouseConnection:
    connection: WarehouseConnection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.POSTGRES,
        name="Flagsmith database",
        config={"source": FLAGSMITH_DATABASE_SOURCE},
    )
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
def rollout_spec(
    admin_user: FFAdminUser,
    multivariate_options: list[MultivariateFeatureOption],
) -> RolloutSpecFactory:
    """Make rollout specs, with every variant weighted 0 unless given."""

    def _make(
        *,
        rollout_percentage: float = 100.0,
        enabled: bool = True,
        variants: list[Variant] | None = None,
        audience: AudienceSpec | None = None,
    ) -> RolloutSpec:
        return RolloutSpec(
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            feature_state_value="control",
            value_type="string",
            variants=(
                [{"id": option.id, "weight": 0.0} for option in multivariate_options]
                if variants is None
                else variants
            ),
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
