from enum import Enum
from typing import List, NotRequired, TypedDict


class EnvMetricsEntities(Enum):
    FEATURES = "features"
    SEGMENTS = "segments"
    WORKFLOWS = "workflows"


class EnvMetricsName(Enum):
    TOTAL_FEATURES = "total_features"
    ENABLED_FEATURES = "enabled_features"
    SEGMENT_OVERRIDES = "segment_overrides"
    OPEN_CHANGE_REQUESTS = "open_change_requests"
    TOTAL_SCHEDULED_CHANGES = "total_scheduled_changes"


class MetricDefinition(TypedDict):
    name: EnvMetricsName
    description: str
    disabled: NotRequired[bool]
    rank: NotRequired[int]
    entity: EnvMetricsEntities


class MetricItemPayload(TypedDict):
    name: str
    description: str
    entity: str
    disabled: NotRequired[bool]
    rank: NotRequired[int]
    value: int


EnvMetricsPayload = List[MetricItemPayload]
