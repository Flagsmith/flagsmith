import prometheus_client

flagsmith_experimentation_warehouse_connection_verifications_total = (
    prometheus_client.Counter(
        "flagsmith_experimentation_warehouse_connection_verifications_total",
        "Outcomes of connection verification attempts against customers' own "
        "data warehouses. `result` label is either `success` or `failure`.",
        ["result"],
    )
)

flagsmith_experimentation_warehouse_delivery_runs_total = prometheus_client.Counter(
    "flagsmith_experimentation_warehouse_delivery_runs_total",
    "Outcomes of per-connection runs delivering buffered event objects to "
    "customers' own data warehouses. `result` label is either `success` or "
    "`failure`; a failed run delivers nothing and is retried on the next tick.",
    ["result"],
)

flagsmith_experimentation_warehouse_delivery_objects_total = prometheus_client.Counter(
    "flagsmith_experimentation_warehouse_delivery_objects_total",
    "Buffered S3 event objects processed by delivery to customers' own data "
    "warehouses. `result` label is `delivered` for objects inserted and "
    "archived, or `rejected` for objects the warehouse refused, which are "
    "moved aside and never retried.",
    ["result"],
)
