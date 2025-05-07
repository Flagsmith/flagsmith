from metrics.types import MetricDefinition, EnvMetricsEntities, EnvMetricsName


TOTAL_FEATURES: MetricDefinition = {
    "name": EnvMetricsName.TOTAL_FEATURES,
    "description": "Total features",
    "entity": EnvMetricsEntities.FEATURES,
    "disabled": False,
    "rank": 1,
}

ENABLED_FEATURES: MetricDefinition = {
    "name": EnvMetricsName.ENABLED_FEATURES,
    "description": "Features enabled",
    "entity": EnvMetricsEntities.FEATURES,
    "disabled": False,
    "rank": 2,
}

SEGMENT_OVERRIDES: MetricDefinition = {
    "name": EnvMetricsName.SEGMENT_OVERRIDES,
    "description": "Segment Overrides",
    "entity": EnvMetricsEntities.SEGMENTS,
    "disabled": False,
    "rank": 3,
}

OPEN_CHANGE_REQUESTS: MetricDefinition = {
    "name": EnvMetricsName.OPEN_CHANGE_REQUESTS,
    "description": "Open change requests",
    "entity": EnvMetricsEntities.CHANGE_REQUESTS,
    "disabled": False,
    "rank": 4,
}

TOTAL_SCHEDULED_CHANGES: MetricDefinition = {
    "name": EnvMetricsName.TOTAL_SCHEDULED_CHANGES,
    "description": "Total scheduled changes",
    "entity": EnvMetricsEntities.SCHEDULED_CHANGES,
    "disabled": False,
    "rank": 5,
}

ALL_METRIC_DEFINITIONS: list[MetricDefinition] = [
    TOTAL_FEATURES,
    ENABLED_FEATURES,
    SEGMENT_OVERRIDES,
    OPEN_CHANGE_REQUESTS,
    TOTAL_SCHEDULED_CHANGES,
]