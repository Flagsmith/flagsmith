# Worker Metrics Helper Testing

This note covers how to test the Story #1 RSS helper.

The helper under test is `get_current_process_max_rss_bytes()`. It reads the
current worker process max RSS high-water mark with
`resource.getrusage(resource.RUSAGE_SELF).ru_maxrss`, converts the Linux KiB
value to bytes, and returns `None` when RSS data cannot be read safely.

## Run The Focused Unit Tests

From the API directory:

```bash
make test opts='tests/unit/metrics/test_unit_worker_metrics.py -n0'
```

If the local shell has an invalid `DEBUG` value, set it explicitly:

```bash
DEBUG=false make test opts='tests/unit/metrics/test_unit_worker_metrics.py -n0'
```

## Run Without Docker

If Docker is unavailable but the API virtualenv is installed:

```bash
DEBUG=false .venv/bin/pytest tests/unit/metrics/test_unit_worker_metrics.py -n0
```

## Run Lint And Format Checks

```bash
.venv/bin/ruff check metrics/worker_metrics.py tests/unit/metrics/test_unit_worker_metrics.py
.venv/bin/ruff format --check metrics/worker_metrics.py tests/unit/metrics/test_unit_worker_metrics.py
```

## Expected Coverage

The unit tests cover:

- successful max-RSS collection
- KiB-to-byte conversion
- use of `resource.RUSAGE_SELF`
- unavailable `resource` module
- missing `ru_maxrss`
- invalid negative RSS values
- unexpected resource errors
