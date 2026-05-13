import prometheus_client

# All metrics are global — refresh and backfill cardinality scales with
# project + environment counts, which would blow up Prometheus storage.
# Drill-down lives in ClickHouse's `system.query_log` (tagged via per-query
# `log_comment` settings) and in structlog events that carry per-project/env
# IDs.

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
