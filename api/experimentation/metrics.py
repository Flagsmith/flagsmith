import prometheus_client

flagsmith_experimentation_warehouse_connection_verifications_total = (
    prometheus_client.Counter(
        "flagsmith_experimentation_warehouse_connection_verifications_total",
        "Outcomes of connection verification attempts against customers' own "
        "data warehouses. `result` label is either `success` or `failure`.",
        ["result"],
    )
)
