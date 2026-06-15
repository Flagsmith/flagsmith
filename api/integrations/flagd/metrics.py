import prometheus_client

flagsmith_flagd_sync_requests_total = prometheus_client.Counter(
    "flagsmith_flagd_sync_requests_total",
    "Number of flagd HTTP sync requests served by the Flagsmith API.",
    ["status"],
)

flagsmith_flagd_document_build_seconds = prometheus_client.Histogram(
    "flagsmith_flagd_document_build_seconds",
    "Wall-clock time spent translating an environment to a flagd document.",
)

flagsmith_flagd_document_size_bytes = prometheus_client.Histogram(
    "flagsmith_flagd_document_size_bytes",
    "Size in bytes of the flagd document returned by the sync endpoint.",
    buckets=(512, 4096, 32_768, 262_144, 2_097_152),
)

flagsmith_flagd_translation_warnings_total = prometheus_client.Counter(
    "flagsmith_flagd_translation_warnings_total",
    "Translation warnings emitted while building flagd documents.",
    ["reason"],
)
