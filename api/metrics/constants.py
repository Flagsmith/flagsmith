from metrics.types import  FeatureMetricsDefinition, SegmentMetricsDefinition, WorkflowsMetricsDefinition, ScheduledMetricsDefinition, MetricItemPayload

FEATURES_DEFINITION: FeatureMetricsDefinition  = {
    "total": {"title": "total_features", "description": "Total features"},
    "enabled": {"title": "enabled_features", "description": "Features enabled"},
}

SEGMENTS_DEFINITION: SegmentMetricsDefinition  = {
    "overrides": {"title": "segment_overrides", "description": "Segment Overrides"},
}

CHANGE_REQUESTS_DEFINITION: WorkflowsMetricsDefinition  = {
    "total": {"title": "open_change_requests", "description": "Open change requests"},
}

SCHEDULED_CHANGES_DEFINITION: ScheduledMetricsDefinition  = {
    "total": {"title": "total_scheduled_changes", "description": "Total scheduled changes"},
}
