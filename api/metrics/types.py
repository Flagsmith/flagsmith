from enum import Enum
from typing import TypedDict, NotRequired


class FeatureMetrics(TypedDict):
    total: int
    enabled: int


class SegmentMetrics(TypedDict):
    overrides: int
    enabled: int


class WorkflowsMetrics(TypedDict):
    open: int


class ScheduledMetrics(TypedDict):
    total: int

class EnvMetricsPayload(TypedDict):
    features: FeatureMetrics
    segments: SegmentMetrics
    change_requests: NotRequired[WorkflowsMetrics]
    scheduled_changes: NotRequired[ScheduledMetrics]

class EnvMetrics(Enum):
    FEATURES = "features"
    SEGMENTS = "segments"
    CHANGE_REQUESTS = "change_requests"
    SCHEDULED_CHANGES = "scheduled_changes"