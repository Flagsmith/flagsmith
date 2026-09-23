import prometheus_client

flagsmith_cohorts_membership_deltas_applied_total = prometheus_client.Counter(
    "flagsmith_cohorts_membership_deltas_applied_total",
    "Total number of cohort membership ledger rows transitioned to their "
    "applied state after the corresponding identity document write. "
    "The `operation` label is either `add` or `remove`.",
    ["operation"],
)

flagsmith_cohorts_csv_syncs_total = prometheus_client.Counter(
    "flagsmith_cohorts_csv_syncs_total",
    "Total number of accepted cohort CSV synchronisations, i.e. uploads that "
    "yielded at least one valid identifier and enqueued a membership sync.",
)

flagsmith_cohorts_csv_sync_identifiers = prometheus_client.Histogram(
    "flagsmith_cohorts_csv_sync_identifiers",
    "Number of unique identifiers extracted per accepted cohort CSV synchronisation.",
    buckets=(10, 100, 1_000, 10_000, 100_000, 1_000_000),
)
