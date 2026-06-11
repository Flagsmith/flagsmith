import prometheus_client

flagsmith_experimentation_exposures_computations_total = prometheus_client.Counter(
    "flagsmith_experimentation_exposures_computations_total",
    "Total experiment exposures summary computations across all experiments, "
    "labelled by result (success or failure).",
    ["result"],
)

flagsmith_experimentation_exposures_computation_duration_seconds = (
    prometheus_client.Histogram(
        "flagsmith_experimentation_exposures_computation_duration_seconds",
        "Duration of one experiment exposures summary computation, dominated "
        "by the ClickHouse exposure-buckets query.",
    )
)
