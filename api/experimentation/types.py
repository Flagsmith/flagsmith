from typing import Literal, TypedDict

from typing_extensions import NotRequired

# TODO: Delete alias as per https://github.com/Flagsmith/flagsmith/issues/7818
from segments.types import SegmentRule as SegmentRuleType

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


class AudienceSegmentSnapshot(TypedDict):
    """One targeted segment as it stood when the audience was configured. Names
    and cohort badges freeze alongside the copied rules, so the stored audience
    keeps describing what the experiment actually launched with. The uuid
    survives the segment's deletion, which its id does not meaningfully."""

    id: int
    uuid: str
    name: str
    is_cohort: bool
    cohort_source_type: str | None


class AudienceSnapshot(TypedDict):
    """A configured audience, self-contained: it carries the compiled rules the
    rollout segment is built from, so that segment is a pure derivation of
    (percentage, snapshot) and never a source of truth.

    Every key is absent exactly when there is no audience, which is the stored
    default and means every identity in the environment is eligible. ``rules``
    is also absent on experiments configured before the snapshot carried it.
    """

    match: NotRequired[str]
    segments: NotRequired[list[AudienceSegmentSnapshot]]
    # The compiled audience rule(s), exactly as appended to the rollout segment.
    rules: NotRequired[list[SegmentRuleType]]
    taken_at: NotRequired[str]


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
