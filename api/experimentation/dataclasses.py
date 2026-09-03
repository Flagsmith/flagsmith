from dataclasses import dataclass
from datetime import datetime

from core.dataclasses import AuthorData
from experimentation.stats import Inference, VariantStats
from experimentation.types import ExposureGranularity
from features.feature_states.models import FeatureValueType
from features.versioning.dataclasses import MultivariateValueChangeSet


@dataclass(frozen=True)
class RolloutSpec:
    enabled: bool
    rollout_percentage: float
    feature_state_value: str
    value_type: FeatureValueType
    multivariate_values: list[MultivariateValueChangeSet]
    author: AuthorData


@dataclass(frozen=True)
class WarehouseEventStats:
    total_events_received: int
    unique_events_count: int


@dataclass(frozen=True)
class WarehouseEventNames:
    events: list[str]
    is_truncated: bool


@dataclass(frozen=True)
class ExposureBucket:
    variant: str
    bucket: datetime
    first_exposed_identities: int
    quarantined: bool = False


@dataclass(frozen=True)
class ExposuresTimeseriesPoint:
    bucket: str
    new_identities: dict[str, int]


@dataclass(frozen=True)
class ExposuresTimeseries:
    granularity: ExposureGranularity
    points: list[ExposuresTimeseriesPoint]


@dataclass(frozen=True)
class ExposuresSummary:
    excluded_identities: int
    timeseries: ExposuresTimeseries


@dataclass(frozen=True)
class ConversionBucket:
    variant: str
    bucket: datetime
    converted_identities: int


@dataclass(frozen=True)
class ConversionsTimeseriesPoint:
    bucket: str
    converted_identities: dict[str, int]


@dataclass(frozen=True)
class ConversionsTimeseries:
    granularity: ExposureGranularity
    points: list[ConversionsTimeseriesPoint]


@dataclass(frozen=True)
class MetricSpec:
    metric_id: int
    event: str
    aggregation: str
    lower_is_better: bool


@dataclass(frozen=True)
class ResultsAggregates:
    """Everything one results refresh reads from the warehouse: the specs it
    was computed from, per-variant identity counts, per metric the per-variant
    ``VariantStats``, and the time-bucketed rows behind the over-time charts.
    Bundled so the keys can't drift."""

    specs: list[MetricSpec]
    exposure_counts: dict[str, int]
    metric_stats: dict[int, dict[str, VariantStats]]
    granularity: ExposureGranularity
    exposure_buckets: list[ExposureBucket]
    # Keyed by metric id, one entry per charted metric.
    conversion_buckets: dict[int, list[ConversionBucket]]


@dataclass(frozen=True)
class MetricResult:
    metric_id: int
    variants: dict[str, VariantStats]
    inference: dict[str, Inference | None]
    # Only occurrence metrics chart a conversion rate; None for the rest.
    conversions_timeseries: ConversionsTimeseries | None


@dataclass(frozen=True)
class ResultsSummary:
    srm_p_value: float | None
    metrics: list[MetricResult]
    # Denominator for the conversion charts, computed in the same run as the
    # metrics so both sides of the rate share one as_of.
    exposures_timeseries: ExposuresTimeseries


@dataclass(frozen=True)
class IngestionInfrastructure:
    bucket_name: str
    stream_name: str
