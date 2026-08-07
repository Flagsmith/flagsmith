---
title: Worker RSS monitoring
sidebar_position: 15
description: Track the peak memory of each Flagsmith API worker process with Prometheus and Grafana.
---

The `flagsmith_worker_rss_bytes` gauge exposes the peak resident-set size of every API worker process, labelled by
process ID. This is the most reliable signal for detecting workers that grow unboundedly (a leak) versus workers that
grow under load and stabilise. Use this page once you have Prometheus scraping configured — see
[Monitoring](./monitoring) for setup.

## Overview

A worker's RSS is the amount of physical memory the operating system currently has mapped for that process. Python-level
profilers tend to miss leaks that live in C extensions, page caches, or the allocator's free lists, so process-level RSS
is often the only reliable signal in production.

`flagsmith_worker_rss_bytes` reports the **high-water mark** — the peak RSS observed for the worker since it started.
The value is read from the `VmHWM` line of `/proc/self/status`, which the Linux kernel maintains atomically. The metric
is updated once per HTTP request handled by the worker.

The gauge has a single label, `pid`, identifying the worker process. When Flagsmith is deployed with multiple gunicorn
workers, you will see one time series per worker.

## Enabling

Set the environment variable:

```bash
PROMETHEUS_ENABLED=true
```

This activates the `WorkerRSSMiddleware` that updates the gauge after each request. No further configuration is required
for single-process deployments.

### Multi-worker deployments

To aggregate metrics across gunicorn workers, set `PROMETHEUS_MULTIPROC_DIR` to a writable directory:

```bash
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
```

The official Flagsmith Docker image sets this automatically. For bare-metal or custom-container deployments, configure
it yourself; otherwise the `/metrics` endpoint will only report data from whichever worker happened to handle the scrape
request.

## Sample output

Scraping `/metrics` on a Flagsmith API with two workers running yields output similar to:

```text
# HELP flagsmith_worker_rss_bytes Maximum RSS (high-water mark) of the worker process in bytes, read from VmHWM in /proc/self/status.
# TYPE flagsmith_worker_rss_bytes gauge
flagsmith_worker_rss_bytes{pid="1234"} 4.8259072e+07
flagsmith_worker_rss_bytes{pid="1235"} 5.2215808e+07
```

Each `pid` corresponds to a live worker. Values are in bytes; the example above shows roughly 46 MiB and 50 MiB
respectively.

## PromQL examples

Useful queries to drop into dashboards or alerts.

**Per-worker peak RSS (raw):**

```promql
flagsmith_worker_rss_bytes
```

**Maximum peak across all workers:**

```promql
max(flagsmith_worker_rss_bytes)
```

**Peak per worker over the last hour:**

```promql
max_over_time(flagsmith_worker_rss_bytes[1h])
```

**Growth indicator — peak RSS now minus peak RSS one hour ago:**

```promql
flagsmith_worker_rss_bytes - flagsmith_worker_rss_bytes offset 1h
```

A consistently positive value across many workers and time windows points to a leak. A value that spikes once after a
deployment and then stays flat is normal — the workers grew under load and levelled off.

## Grafana panel

A reasonable starting point for a "Worker memory" panel:

| Setting       | Value                                        |
| ------------- | -------------------------------------------- |
| Visualisation | Time series                                  |
| Query         | `flagsmith_worker_rss_bytes`                 |
| Legend        | `{{pid}}`                                    |
| Unit          | bytes (IEC) — Grafana renders as KiB/MiB/GiB |
| Stacking      | Disabled — each worker is independent        |

Add a second panel showing `max(flagsmith_worker_rss_bytes)` for a single-number overview.

## Interpretation notes

The metric is a high-water mark, not a current reading. Understanding the implications avoids false alerts.

- **The value never decreases for a given PID.** Once a worker has peaked at a particular RSS, the gauge for that PID
  will stay at that value until the worker process exits. Recovery is observed through PID rotation: when a worker is
  recycled (for example, by gunicorn's `--max-requests` setting or by a deployment), the old PID's time series goes
  stale and a new PID appears with a fresh, lower value.
- **Steady high RSS is normal after warm-up.** A worker that loads caches at startup will reach its steady-state peak
  quickly and stay there. This appears as a flat line in Grafana, not a leak.
- **Periodic large workloads inflate the peak.** If a worker occasionally processes a large payload (for example, a bulk
  export), the gauge will pin at that peak for the rest of the worker's lifetime even after the memory has been freed.
  Investigate via PID rotation rather than waiting for the value to fall.
- **Leak signature.** A genuine leak shows up as the peak climbing across many worker restarts — every newly forked
  worker reaches a higher peak than its predecessor.
- **Quirk: parent-process inheritance.** On Linux, the kernel may preserve the high-water mark across `execve()`, so a
  freshly spawned worker can report a non-zero baseline inherited from its parent. Treat the first scrape after a
  deployment as informational rather than a true zero.

## Related documentation

- [Metrics reference](./metrics) — full catalogue of exported Prometheus metrics.
- [Monitoring](./monitoring) — enabling `/metrics` and other vendor integrations.
