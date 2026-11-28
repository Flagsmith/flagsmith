import prometheus_client

flagsmith_flag_bisect_signals_total = prometheus_client.Counter(
    "flagsmith_flag_bisect_signals_total",
    "Request outcomes reported by SDK-side apps for Flag Bisect. "
    "`outcome` label is either `ok` or `failed`.",
    ["outcome"],
)

flagsmith_flag_bisect_incidents_total = prometheus_client.Counter(
    "flagsmith_flag_bisect_incidents_total",
    "Incidents opened by the Flag Bisect Sentinel after a failure-rate shift.",
)

flagsmith_flag_bisect_probes_total = prometheus_client.Counter(
    "flagsmith_flag_bisect_probes_total",
    "Canary probes decided by the Flag Bisect Judge. `verdict` label is one of "
    "`healed`, `not_healed`, `inconclusive` or `harmful`.",
    ["verdict"],
)

flagsmith_flag_bisect_conclusions_total = prometheus_client.Counter(
    "flagsmith_flag_bisect_conclusions_total",
    "Incidents that reached a conclusion. `result` label is one of `identified`, "
    "`not_a_flag_change`, `inconclusive` or `aborted`.",
    ["result"],
)
