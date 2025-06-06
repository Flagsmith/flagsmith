from metrics.types import EnvMetricsEntities, EnvMetricsName, MetricDefinition

TOTAL_FEATURES: MetricDefinition = {
    "name": EnvMetricsName.TOTAL_FEATURES,
    "description": "Total features",
    "entity": EnvMetricsEntities.FEATURES,
    "rank": 1,
}

ENABLED_FEATURES: MetricDefinition = {
    "name": EnvMetricsName.ENABLED_FEATURES,
    "description": "Features enabled",
    "entity": EnvMetricsEntities.FEATURES,
    "rank": 2,
}

SEGMENT_OVERRIDES: MetricDefinition = {
    "name": EnvMetricsName.SEGMENT_OVERRIDES,
    "description": "Segment overrides",
    "entity": EnvMetricsEntities.SEGMENTS,
    "rank": 3,
}

IDENTITY_OVERRIDES: MetricDefinition = {
    "name": EnvMetricsName.IDENTITY_OVERRIDES,
    "description": "Identity overrides",
    "entity": EnvMetricsEntities.IDENTITIES,
    "rank": 4,
}

OPEN_CHANGE_REQUESTS: MetricDefinition = {
    "name": EnvMetricsName.OPEN_CHANGE_REQUESTS,
    "description": "Open change requests",
    "entity": EnvMetricsEntities.WORKFLOWS,
    "rank": 5,
}

TOTAL_SCHEDULED_CHANGES: MetricDefinition = {
    "name": EnvMetricsName.TOTAL_SCHEDULED_CHANGES,
    "description": "Scheduled changes",
    "entity": EnvMetricsEntities.WORKFLOWS,
    "rank": 6,
}


DEFAULT_METRIC_DEFINITIONS: list[MetricDefinition] = [
    TOTAL_FEATURES,
    ENABLED_FEATURES,
    SEGMENT_OVERRIDES,
    IDENTITY_OVERRIDES,
]

WORKFLOW_METRIC_DEFINITIONS: list[MetricDefinition] = [
    OPEN_CHANGE_REQUESTS,
    TOTAL_SCHEDULED_CHANGES,
]
