import prometheus_client

CACHE_HIT = "CACHE_HIT"
CACHE_MISS = "CACHE_MISS"

flagsmith_environment_document_cache_result = prometheus_client.Counter(
    "flagsmith_environment_document_cache_result",
    "Results of cache retrieval for environment document (hit or miss)",
    ["api_key", "result"],
)
