import prometheus_client

# Metrics are global. Per-project / per-env drill-down lives in CH's
# `system.query_log` (via `log_comment`) and in the structlog events.

flagsmith_segment_membership_backfill_identities_total = prometheus_client.Counter(
    "flagsmith_segment_membership_backfill_identities_total",
    "Total identities mirrored from Dynamo to ClickHouse by the segment-membership backfill task across all environments.",
)

flagsmith_segment_membership_backfill_duration_seconds = prometheus_client.Histogram(
    "flagsmith_segment_membership_backfill_duration_seconds",
    "Duration of a segment-membership backfill for one environment.",
)

flagsmith_segment_membership_refresh_duration_seconds = prometheus_client.Histogram(
    "flagsmith_segment_membership_refresh_duration_seconds",
    "Duration of a single segment-membership count-refresh run for one project.",
)

flagsmith_segment_membership_refresh_failures_total = prometheus_client.Counter(
    "flagsmith_segment_membership_refresh_failures_total",
    "Total segment-membership refresh runs that failed for any reason.",
)

flagsmith_segment_membership_read_duration_seconds = prometheus_client.Histogram(
    "flagsmith_segment_membership_read_duration_seconds",
    "Duration of a single segment membership page read.",
)
