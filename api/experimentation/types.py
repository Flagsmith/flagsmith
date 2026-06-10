from typing import Literal, TypedDict

ExposureGranularity = Literal["hour", "day"]


class ExposureVariantData(TypedDict):
    key: str
    identities: int
    share: float
    is_control: bool
    first_exposure: str
    last_exposure: str


class ExposureTimeseriesPoint(TypedDict):
    bucket: str
    cumulative_identities: dict[str, int]


class ExposureTimeseries(TypedDict):
    granularity: ExposureGranularity
    points: list[ExposureTimeseriesPoint]


class ExposuresPayload(TypedDict):
    """An experiment's exposure window, as persisted on snapshots and served
    by the exposures API."""

    total_identities: int
    excluded_identities: int
    days_of_data: int
    variants: list[ExposureVariantData]
    timeseries: ExposureTimeseries


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
