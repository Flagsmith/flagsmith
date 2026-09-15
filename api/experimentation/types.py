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


class ExperimentMetadata(TypedDict):
    """Present on a feature state only while the experiment is running."""

    id: int
    name: str
    in_experiment: bool


class FeatureStateMetadata(TypedDict, total=False):
    experiment: ExperimentMetadata


FEATURE_STATE_METADATA_SCHEMA: dict[str, object] = {
    "type": "object",
    "description": "Absent when the feature state carries no metadata.",
    "properties": {
        "experiment": {
            "type": "object",
            "description": "Present only while the feature's experiment is running.",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "in_experiment": {
                    "type": "boolean",
                    "description": "Whether the identity is enrolled in the experiment.",
                },
            },
            "required": ["id", "name", "in_experiment"],
        },
    },
}


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
