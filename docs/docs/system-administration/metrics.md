# Prometheus metrics

Flagsmith exports Prometheus metrics described below.

## `flagsmith_build_info` gauge

Flagsmith version and build information.

Labels:
 - `ci_commit_sha`
 - `version`

## `flagsmith_environment_document_cache_queries` counter

Results of cache retrieval for environment document. `result` label is either `hit` or `miss`.

Labels:
 - `result`

## `flagsmith_http_server_request_duration_seconds` histogram

HTTP request duration in seconds.

Labels:
 - `route`
 - `method`
 - `response_status`

## `flagsmith_http_server_requests` counter

Total number of HTTP requests.

Labels:
 - `route`
 - `method`
 - `response_status`

## `flagsmith_http_server_response_size_bytes` histogram

HTTP response size in bytes.

Labels:
 - `route`
 - `method`
 - `response_status`

## `flagsmith_task_processor_enqueued_tasks` counter

Total number of enqueued tasks.

Labels:
 - `task_identifier`

## `flagsmith_task_processor_finished_tasks` counter

Total number of finished tasks. Only collected by Task Processor. `task_type` label is either `recurring` or `standard`.

Labels:
 - `task_identifier`
 - `task_type`
 - `result`

## `flagsmith_task_processor_task_duration_seconds` histogram

Task processor task duration in seconds. Only collected by Task Processor. `task_type` label is either `recurring` or `standard`.

Labels:
 - `task_identifier`
 - `task_type`
 - `result`

