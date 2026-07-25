from typing import Literal, TypedDict

ExposureGranularity = Literal["hour", "day"]


class MetricDefinitionV1(TypedDict):
    """The recipe a metric is computed from.

    Versioned so the shape can evolve; see ``metric_definitions`` for the
    registry of supported versions and their validators. v1 captures the
    warehouse event whose occurrences/values the metric aggregates.
    """

    version: int
    event: str


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


class ClickHouseConfig(TypedDict):
    host: str
    port: int
    database: str
    username: str
    secure: bool


CLICKHOUSE_DEFAULTS: ClickHouseConfig = {
    "host": "",
    "port": 9440,
    "database": "flagsmith",
    "username": "default",
    "secure": True,
}


class ClickHouseCredentials(TypedDict):
    password: str
