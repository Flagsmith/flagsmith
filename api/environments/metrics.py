import prometheus_client

from environments.dynamodb.constants import (
    COMPRESSION_RATIO_HISTOGRAM_BUCKETS,
    DOCUMENT_SIZE_HISTOGRAM_BUCKETS,
)

CACHE_HIT = "CACHE_HIT"
CACHE_MISS = "CACHE_MISS"

flagsmith_environment_document_cache_queries_total = prometheus_client.Counter(
    "flagsmith_environment_document_cache_queries_total",
    "Results of cache retrieval for environment document. `result` label is either `hit` or `miss`.",
    ["result"],
)

flagsmith_dynamo_environment_document_size_bytes = prometheus_client.Histogram(
    "flagsmith_dynamo_environment_document_size_bytes",
    "Size of environment documents written to DynamoDB.",
    ["table", "compressed"],
    buckets=DOCUMENT_SIZE_HISTOGRAM_BUCKETS,
)

flagsmith_dynamo_environment_document_compression_ratio = prometheus_client.Histogram(
    "flagsmith_dynamo_environment_document_compression_ratio",
    "Compression ratio (compressed_size / uncompressed_size) of environment documents.",
    ["table"],
    buckets=COMPRESSION_RATIO_HISTOGRAM_BUCKETS,
)
