from enum import Enum
from typing import List, NotRequired, TypedDict


class MetricDefinition(TypedDict):
    title: str
    description: str
    disabled: NotRequired[bool]


class MetricItemPayload(MetricDefinition):
    value: int


class FeatureMetricsDefinition(TypedDict):
    total: MetricDefinition
    enabled: MetricDefinition


class SegmentMetricsDefinition(TypedDict):
    overrides: MetricDefinition


class WorkflowsMetricsDefinition(TypedDict):
    total: MetricDefinition


class ScheduledMetricsDefinition(TypedDict):
    total: MetricDefinition


class EnvMetricsPayload(TypedDict):
    features: List[MetricItemPayload]
    segments: List[MetricItemPayload]
    change_requests: NotRequired[List[MetricItemPayload]]
    scheduled_changes: NotRequired[List[MetricItemPayload]]


class EnvMetrics(Enum):
    FEATURES = "features"
    SEGMENTS = "segments"
    CHANGE_REQUESTS = "change_requests"
    SCHEDULED_CHANGES = "scheduled_changes"
