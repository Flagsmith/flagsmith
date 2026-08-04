import prometheus_client

flagsmith_cohorts_membership_deltas_applied_total = prometheus_client.Counter(
    "flagsmith_cohorts_membership_deltas_applied_total",
    "Total number of cohort membership deltas applied to identity documents. "
    "The `operation` label is either `add` or `remove`.",
    ["operation"],
)
