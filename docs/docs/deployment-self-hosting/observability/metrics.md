---
title: Metrics
sidebar_label: Metrics
sidebar_position: 20
---

## Prometheus

To enable the Prometheus `/metrics` endpoint, set the `PROMETHEUS_ENABLED` environment variable to `true`.

When enabled, Flagsmith serves the `/metrics` endpoint on port 9100.

The metrics provided by Flagsmith are described below.


### `flagsmith_build_info`

Gauge.

Flagsmith version and build information.

Labels:
 - `ci_commit_sha`
 - `version`

### `flagsmith_dynamo_environment_document_compression_ratio`

Histogram.

Compression ratio (compressed_size / uncompressed_size) of environment documents.

Labels:
 - `table`

### `flagsmith_dynamo_environment_document_size_bytes`

Histogram.

Size of environment documents written to DynamoDB.

Labels:
 - `table`
 - `compressed`

### `flagsmith_environment_document_cache_queries`

Counter.

Results of cache retrieval for environment document. `result` label is either `hit` or `miss`.

Labels:
 - `result`

### `flagsmith_http_server_request_duration_seconds`

Histogram.

HTTP request duration in seconds.

Labels:
 - `route`
 - `method`
 - `response_status`

### `flagsmith_http_server_requests`

Counter.

Total number of HTTP requests.

Labels:
 - `route`
 - `method`
 - `response_status`

### `flagsmith_http_server_response_size_bytes`

Histogram.

HTTP response size in bytes.

Labels:
 - `route`
 - `method`
 - `response_status`

### `flagsmith_task_processor_enqueued_tasks`

Counter.

Total number of enqueued tasks.

Labels:
 - `task_identifier`

### `flagsmith_task_processor_finished_tasks`

Counter.

Total number of finished tasks. Only collected by Task Processor. `task_type` label is either `recurring` or `standard`.

Labels:
 - `task_identifier`
 - `task_type`
 - `result`

### `flagsmith_task_processor_task_duration_seconds`

Histogram.

Task processor task duration in seconds. Only collected by Task Processor. `task_type` label is either `recurring` or `standard`.

Labels:
 - `task_identifier`
 - `task_type`
 - `result`

