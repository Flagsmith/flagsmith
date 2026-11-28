from typing import Annotated, Literal

from pydantic import Field
from typing_extensions import TypedDict

ExposureGranularity = Literal["hour", "day"]


class MetricDefinitionV1(TypedDict):
    """The warehouse event whose occurrences or values the metric aggregates."""

    version: Literal[1]
    event: Annotated[str, Field(min_length=1)]


MetricDefinition = MetricDefinitionV1


class MetricExperimentResult(TypedDict):
    """A lightweight view of an experiment using a metric, as returned in the
    metric's ``experiments`` field."""

    id: int
    name: str
    status: str


class SnowflakeConfig(TypedDict):
    account_identifier: str
    warehouse: str
    database: str
    schema: str
    role: str
    user: str


SNOWFLAKE_DEFAULTS: SnowflakeConfig = {
    "account_identifier": "",
    "warehouse": "COMPUTE_WH",
    "database": "FLAGSMITH",
    "schema": "ANALYTICS",
    "role": "FLAGSMITH_LOADER",
    "user": "FLAGSMITH_SERVICE",
}


class SnowflakeCredentials(TypedDict):
    private_key: str


class ClickHouseConfig(TypedDict):
    host: str
    # The HTTP(S) interface port, used for verification and delivery alike.
    port: int
    database: str
    username: str
    secure: bool


CLICKHOUSE_DEFAULTS: ClickHouseConfig = {
    "host": "",
    "port": 8443,
    "database": "flagsmith_exp",
    "username": "default",
    "secure": True,
}


class ClickHouseCredentials(TypedDict):
    password: str


class DatabricksConfig(TypedDict):
    host: str
    workspace_id: str
    region: str
    warehouse_id: str
    catalog: str
    schema: str


DATABRICKS_DEFAULTS: DatabricksConfig = {
    "host": "",
    "workspace_id": "",
    "region": "",
    "warehouse_id": "",
    "catalog": "",
    "schema": "flagsmith_exp",
}


class DatabricksCredentials(TypedDict):
    client_id: str
    client_secret: str


class PostgresConfig(TypedDict):
    host: str
    port: int
    database: str
    schema: str
    username: str
    sslmode: str


POSTGRES_DEFAULTS: PostgresConfig = {
    "host": "",
    "port": 5432,
    "database": "",
    "schema": "flagsmith_exp",
    "username": "",
    "sslmode": "require",
}


class PostgresCredentials(TypedDict):
    password: str


class RejectedSDKEvent(TypedDict):
    index: int
    error: str


class SDKEventBatchResult(TypedDict):
    accepted: int
    rejected: list[RejectedSDKEvent]
