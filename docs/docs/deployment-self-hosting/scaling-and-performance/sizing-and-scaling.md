---
title: Sizing and Scaling
description: How big to start, what to watch, when to scale up. Workload-driven sizing for self-hosted Flagsmith.
sidebar_position: 80
---

How big to start, what to watch, when to scale. Sizing depends on how your application uses Flagsmith: pick a pattern,
read your tier.

## Quick start

1. **[Pick a pattern](#pick-your-workload-pattern)**: A (logged-in users), B (server-side local cache), or C (anonymous
   flag check).
2. Estimate peak Flagsmith RPS using the [worked examples](#worked-examples).
3. Read your tier from the [tier reference](#tier-reference).
4. If you'll run any **Server-side cached (B)** traffic, set `CACHE_ENVIRONMENT_DOCUMENT_SECONDS=60`. Off by default;
   biggest single sizing lever.
5. Watch the [metrics](#metrics-to-monitor) and follow the [decision tree](#scaling-decision-tree) when a threshold
   trips.

:::tip How to scale

**API**: add workers, keep each at 1 vCPU / 2 GB (2 vCPU / 4 GB at Large+). **Database**: bump CPU / memory / IOPS, add
a read replica at Large.

:::

## Pick your workload pattern

Most deployments are one of A, B, or C. Mixed traffic: see [Example 5](#example-5-mixed-traffic-patterns-a--b).

### A: App with logged-in users

App sends a user ID (plus traits like country, plan, role) and Flagsmith returns that user's personalised flags. Works
the same whether the client is mobile, web, desktop, or a server acting for a user.

**You're here if:**

-   Web app with sign-in (React, Vue, Angular, server-rendered)
-   iOS, Android, React Native, Flutter app with user accounts
-   Backend evaluating flags for a known end-user in remote-evaluation mode
-   Targeting by user attribute, plan, region, cohort, or A/B bucket

**Cost shape:**

-   Each call: moderate work. Looks up user, evaluates segments, returns the flag set.
-   Response: usually a few KB. Many segments / traits can push it past 50 KB.
-   Volume scales with sessions per day. Baseline ≈ **2 calls per session** (open + auth), plus any refetches your
    client triggers.

### B: Server-side service with local cache

Backend polls Flagsmith every 60 seconds for the full environment snapshot, then evaluates flags locally. No round-trip
per flag check.

:::tip Local or remote evaluation?

This pattern assumes _local evaluation_. Unsure which mode fits your application?
[Learn more here](/integrating-with-flagsmith/integration-overview#local-evaluation-mode).

:::

**You're here if:**

-   Node.js, Python, Java, Go, .NET, Ruby, Elixir, or Rust backend using the SDK in _local-evaluation_ mode
-   Batch jobs evaluating flags at high throughput
-   Microservices needing sub-millisecond flag checks

**Cost shape:**

-   Each poll is the heaviest thing Flagsmith does. It returns the entire environment and runs many database joins to
    build it.
-   Polling rate drives load, not user volume. 30 pods × 60 s poll = 0.5 RPS to Flagsmith, regardless of how many user
    requests the backend handles.
-   Hardest on the database by default. [Enabling the cache](#cache-configuration) moves most of the cost.

<details>
<summary>SDK polling defaults</summary>

| SDK                                             | Default                                        |
| ----------------------------------------------- | ---------------------------------------------- |
| Python, Node.js, Java, Ruby, .NET, Elixir, Rust | 60 s                                           |
| Go                                              | On-demand (no background poll unless opted in) |
| PHP                                             | No local-evaluation polling                    |

</details>

### C: Anonymous flag check

Flag check without a user identity: public pages, marketing experiments, default-vs-variant rollouts.

**You're here if:**

-   Marketing site with simple A/B tests
-   Public content varying by flag, not by user
-   SDK requests without identity context

**Cost shape:**

-   Each call: a flag-list lookup. Cheapest of the three.
-   Response: small (1–5 KB).
-   Volume scales with page views.

## Worked examples

### Example 1: small SaaS web app (Pattern A)

> "100,000 monthly active users on our web product. Most users open the app once a day on average. About 5% of usage
> falls in our peak hour."

| Step               | Calculation                                | Value     |
| ------------------ | ------------------------------------------ | --------- |
| Daily sessions     | 100,000 MAU × 1 session/day                | 100,000   |
| Peak-hour sessions | 100,000 × 5%                               | 5,000     |
| Peak Flagsmith RPS | 5,000 sessions × 2 calls/session ÷ 3,600 s | ≈ 2.8     |
| **Tier**           | Pattern A: below 10 RPS                    | **Small** |

### Example 2: backend service polling Flagsmith (Pattern B)

> "30 backend pods running the Node.js SDK in local-evaluation mode with the default 60-second polling interval, all
> sharing one Flagsmith environment."

| Step                          | Calculation                  | Value     |
| ----------------------------- | ---------------------------- | --------- |
| Polls per second to Flagsmith | 30 pods ÷ 60 s               | 0.5 RPS   |
| **Tier**                      | Below Pattern B's 1 RPS band | **Small** |

**How the numbers move:**

| If you change…                                  | New RPS | New tier |
| ----------------------------------------------- | ------- | -------- |
| Pods scale up to 300 (same one environment)     | 5 RPS   | Medium   |
| Poll interval dropped to 10 s (default is 60 s) | 3 RPS   | Medium   |
| Both, 300 pods polling every 10 s               | 30 RPS  | Large    |

:::caution Watch poll rate, not pod count

A 10× faster poll has the same effect as 10× more pods. With server-side environment-document caching on, both controls
matter much less: the database only sees one fetch per cache TTL regardless of how many pods are asking.

:::

### Example 3: large consumer app at scale (Pattern A)

> "5 million MAU on our consumer app (web + mobile combined), 2 sessions per user per day average, 5% peak-hour
> concentration, our SDKs refresh flags after login and on user actions, ≈ 4 Flagsmith calls per session."

| Step               | Calculation              | Value           |
| ------------------ | ------------------------ | --------------- |
| Daily sessions     | 5,000,000 × 2            | 10 million      |
| Peak-hour sessions | 10 M × 5%                | 500,000         |
| Peak Flagsmith RPS | 500,000 × 4 ÷ 3,600      | ≈ 555           |
| **Tier**           | Pattern A: above 200 RPS | **Extra-Large** |

### Example 4: marketing landing page (Pattern C)

> "Our marketing site gets 50,000 visits per day. Each visit does one anonymous flag check on the landing page."

| Step               | Calculation                  | Value     |
| ------------------ | ---------------------------- | --------- |
| Daily flag checks  | 50,000                       | 50,000    |
| Peak-hour calls    | 50,000 × 5%                  | 2,500     |
| Peak Flagsmith RPS | 2,500 ÷ 3,600                | ≈ 0.7     |
| **Tier**           | Pattern C: well below 50 RPS | **Small** |

### Example 5: mixed traffic (Patterns A + B)

> "We have a SaaS web app with 500,000 MAU (logged-in users) AND a back-end service running 10 pods in local-evaluation
> mode at the default 60-second poll. The web app makes ~3 calls per session, peak hour is 5% of daily."

**Step 1: estimate each pattern separately:**

| Pattern              | Calculation                                                     | Peak RPS   |
| -------------------- | --------------------------------------------------------------- | ---------- |
| **A** (web sessions) | 500,000 MAU × 1 session/day × 5% peak ÷ 3,600 × 3 calls/session | ≈ 21 RPS   |
| **B** (polling)      | 10 pods ÷ 60 s                                                  | ≈ 0.17 RPS |

**Step 2: pick the tier on each axis:**

| Axis                                    | Numbers                                  | Tier from that axis           |
| --------------------------------------- | ---------------------------------------- | ----------------------------- |
| API tier (driven by total RPS)          | 21 + 0.17 ≈ 21 RPS                       | **Medium** (A 10–50 RPS band) |
| Database tier (driven by combined load) | A is light per call; B is heavy per call | **Medium**                    |

:::tip Rule of thumb for mixed traffic

Estimate each pattern separately, add the RPS values, then pick the higher of the two tiers, whichever axis is more
demanding sets your starting size. Almost always: the API tier is driven by total RPS; the database tier is driven by
the heaviest pattern (B if you run any).

:::

## Tier reference

Choose the equivalent compute instance type in your cloud (AWS Aurora, Azure Database for PostgreSQL Flexible Server,
Google Cloud SQL, or any self-managed PostgreSQL). The numbers below are minimum non-burstable specs; oversize if in
doubt.

### What's running in a Flagsmith deployment

| Component          | What it does                                                                                                                                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **API**            | Stateless Python web service. Serves SDK and dashboard requests. Each worker is a pod (Kubernetes) or task (ECS). Scaled horizontally with an autoscaler.                            |
| **Frontend**       | Static admin dashboard. Stateless; not in the SDK hot path. Light load even at large deployments; one or two replicas behind a load balancer is enough. No sticky sessions required. |
| **Database**       | PostgreSQL. Stores flags, segments, environments, identities, and audit data. Scaled vertically. Add a read replica at Large (see [Database replicas](#database-replicas)).          |
| **Task processor** | Separate worker that runs background jobs (webhook delivery, audit log writes, scheduled tasks). Same image as the API, run with a different command. Sized similarly at every tier. |
| **SSE** (optional) | Server-Sent Events service, pushes real-time flag updates to connected SDKs. Only deployed if you use Flagsmith's real-time updates feature.                                         |

### Small

**Workload bands:** A ≤ 10 RPS · B ≤ 1 RPS · C ≤ 50 RPS

Entry-level production. A typical first-year self-hosted deployment.

| Component      | Recommendation                                                                                      |
| -------------- | --------------------------------------------------------------------------------------------------- |
| API            | 2 workers at 1 vCPU / 2 GB · Autoscale min 2 / max 5 / target 60% CPU · Gunicorn defaults are fine  |
| Database       | 2 vCPU / 8 GB · 1,000 IOPS provisioned · Non-burstable instance class · 30 GB storage · HA optional |
| Task processor | 1 worker at 1 vCPU / 2 GB                                                                           |
| Load balancer  | Standard cloud LB                                                                                   |

### Medium

**Workload bands:** A 10–50 RPS · B 1–10 RPS · C 50–300 RPS

Standard production. Most self-hosted deployments serving active user populations land here.

| Component      | Recommendation                                                                                                                                           |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API            | 4–6 workers at 1 vCPU / 2 GB, or 3 workers at 2 vCPU / 4 GB · Autoscale min 4 / max 15 / target 60% CPU · Raise gunicorn worker count for large payloads |
| Database       | 4 vCPU / 16 GB · 3,000 IOPS provisioned · Non-burstable · 50 GB storage · HA recommended (multi-AZ writer) · Env-document cache mandatory for Pattern B  |
| Task processor | 1–2 workers at 1 vCPU / 2 GB                                                                                                                             |
| Load balancer  | Standard cloud LB · Dedicated SSE pod (1–2) if using real-time updates                                                                                   |

### Large

**Workload bands:** A 50–200 RPS · B 10–50 RPS · C 300–1,500 RPS

Heavy production. Customer-facing applications at scale.

| Component      | Recommendation                                                                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| API            | 10–15 workers at 1 vCPU / 2 GB, or 5–8 at 2 vCPU / 4 GB · Autoscale min 6 / max 25 / target 60% CPU · Tune gunicorn workers + timeout for Pattern A large payloads |
| Database       | 8 vCPU / 32 GB, memory-optimised preferred · 6,000 IOPS provisioned · HA mandatory · **Read replica required for Pattern B** · Cache in `PERSISTENT` mode          |
| Task processor | 2 workers at 1 vCPU / 2 GB                                                                                                                                         |
| Load balancer  | Standard cloud LB · Dedicated SSE pods (2+) if using real-time updates                                                                                             |

### Extra-Large

**Workload bands:** A > 200 RPS · B > 50 RPS · C > 1,500 RPS

Very heavy production. If you expect to operate at this scale, please contact the Flagsmith team so we can validate the
configuration against your specific workload.

| Component      | Recommendation                                                                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| API            | 20–30+ workers at 2 vCPU / 4 GB · Autoscale min 10 / max 50 / target 60% CPU                                                                                       |
| Database       | 16 vCPU / 64 GB+ · 10,000+ IOPS · Connection pool required (PgBouncer / RDS Proxy / Cloud SQL Auth Proxy) · 2+ read replicas; consider cross-region · HA mandatory |
| Task processor | 2–4 workers at 1 vCPU / 2 GB                                                                                                                                       |
| Load balancer  | Dedicated SSE pods (3+) · Consider CDN / Edge Proxy in front of API for read-heavy paths                                                                           |

### Headroom rules

Apply on top of the tier you've chosen. These are the safety margins that absorb spikes.

-   **API: provision ≥ 2× your hourly peak RPS.** Per-minute spikes typically run 1–2× the hourly average peak. 2×
    headroom covers them.
-   **Database CPU: target ≤ 50% peak.** Leaves room for autovacuum, ad-hoc admin queries, and unexpected bursts.
-   **IOPS: provision ≥ 2× your peak read+write IOPS.** IOPS ceilings throttle silently, better to overshoot.
-   **Autoscale max: 4× the starting worker count is enough for most cases.** Wider range if you expect spikes.

## Cache configuration

Flagsmith ships with several caches, all **disabled by default**. Enabling them is the cheapest single change you can
make to reduce database load, often by an order of magnitude.

:::tip Day-1 setting for any production deployment

```
CACHE_ENVIRONMENT_DOCUMENT_SECONDS=60
```

With Pattern B traffic, this typically drops database load by ~10× without any other change.

:::

### Cache reference

| Environment variable                    | Default    | Recommended (Medium+)                                        | What it does                                                                                                                                         |
| --------------------------------------- | ---------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CACHE_ENVIRONMENT_DOCUMENT_SECONDS`    | `0` (off)  | `60`                                                         | Cache the heavy server-side SDK environment-document fetch. PostgreSQL hit at most once per TTL per environment.                                     |
| `CACHE_ENVIRONMENT_DOCUMENT_BACKEND`    | Database   | `LocMemCache` at Small / Medium, Redis / Memcached at Large+ | Default keeps the cache in PostgreSQL, cheap hits but still touches the DB. Switch to pod-local memory or an external cache for true off-DB caching. |
| `CACHE_ENVIRONMENT_DOCUMENT_MODE`       | `EXPIRING` | `PERSISTENT` at Large+                                       | Persistent mode survives pod restarts; warm-up cost amortised across the deployment.                                                                 |
| `GET_IDENTITIES_ENDPOINT_CACHE_SECONDS` | `0` (off)  | `30–60`                                                      | Cache the personalised response from a _GET_ identity request. _POST_ identity (which updates traits) always bypasses the cache.                     |

### Cache backend trade-offs

These options set `CACHE_ENVIRONMENT_DOCUMENT_BACKEND`. See
[Caching Strategies](/deployment-self-hosting/core-configuration/caching-strategies) for the backend / location
configuration, including a worked Memcached example.

-   **Database (default).** Shared across pods. Cache hits still touch PostgreSQL. Fine through Medium.
-   **LocMemCache.** Pod-local. Zero DB round-trip, but each pod warms separately and memory cost scales with pod count.
    Best at Small / Medium with a small number of pods.
-   **Redis / Memcached.** Shared, fast, off-DB. Adds a service you operate. Right at Large+.

### When to keep TTL short or skip the cache

-   **Kill-switch flags.** Flagsmith invalidates the cache on flag changes, but TTL is the worst-case wait. For
    incidents, use TTL ≤ 10 s.
-   **Compliance / access-control flags.** Stale flags could expose protected functionality. Consider a non-cached path.
-   **Apps mutating traits mid-session.** The GET-identity cache returns the same response per identifier until TTL
    expires. Use POST identity (always fresh) or skip the cache.
-   **SDKs polling slowly (5+ min).** Server cache rarely helps. The SDK won't ask within the TTL anyway.

## Database replicas

Required for Pattern B at the Large tier and above, optional at Medium. Flagsmith automatically routes the heaviest read
paths (environment-document fetches, identity lookups) to a configured replica.

Set the connection URLs via environment variables on the API:

| Variable                                       | Purpose                                                                                                                                                                                          |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `REPLICA_DATABASE_URLS`                        | Comma-separated list of replica PostgreSQL URLs. Used for local (same-region) replicas.                                                                                                          |
| `REPLICA_DATABASE_URLS_DELIMITER`              | Override the `,` delimiter if any of your passwords contain commas.                                                                                                                              |
| `CROSS_REGION_REPLICA_DATABASE_URLS`           | Comma-separated list of replica URLs in other regions. Used only when all local replicas are offline (cross-region latency is unfavourable as a load-distribution choice).                       |
| `CROSS_REGION_REPLICA_DATABASE_URLS_DELIMITER` | Override the cross-region delimiter for the same reason.                                                                                                                                         |
| `REPLICA_READ_STRATEGY`                        | `DISTRIBUTED` (default) spreads reads evenly across replicas. `SEQUENTIAL` uses fallback order (primary first, then secondary, etc.) — a replica is only used if all preceding ones are offline. |

`REPLICA_DATABASE_URLS` and `CROSS_REGION_REPLICA_DATABASE_URLS` can be set together or independently. Both strategies
apply to both sets.

Example:

```
REPLICA_DATABASE_URLS=postgres://user:password@replica1.host:5432/flagsmith,postgres://user:password@replica2.host:5432/flagsmith
REPLICA_READ_STRATEGY=DISTRIBUTED
```

Once you reach the Extra-Large tier (or sustained > 70% of `max_connections`), also put a connection pool in front of
the writer: [PgBouncer](https://www.pgbouncer.org/), AWS RDS Proxy, or Cloud SQL Auth Proxy. The pool absorbs connection
churn from gunicorn worker recycles and SDK polling fan-out.

## Worker tuning

### API (gunicorn)

Each API pod runs gunicorn. Tune worker count and timeout when the [decision tree](#scaling-decision-tree) says so, or
when Pattern A responses run large (many segments / traits per identity) and the default 30 s timeout starts killing
slow requests.

| Variable              | Default | What it controls                                                                                                                              |
| --------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `GUNICORN_WORKERS`    | `3`     | Worker processes per pod. Raise to handle more concurrent requests.                                                                           |
| `GUNICORN_THREADS`    | `2`     | Threads per worker.                                                                                                                           |
| `GUNICORN_TIMEOUT`    | `30`    | Seconds a worker can spend on a single request before being killed. Raise for large-payload deployments to avoid LB-level 5xx during a spike. |
| `GUNICORN_KEEP_ALIVE` | `2`     | HTTP keep-alive timeout in seconds.                                                                                                           |

### Task processor

| Variable                           | Default | What it controls                                                                               |
| ---------------------------------- | ------- | ---------------------------------------------------------------------------------------------- |
| `TASK_PROCESSOR_NUM_THREADS`       | `5`     | Concurrent task threads per pod. Raise if you see backlog growing.                             |
| `TASK_PROCESSOR_QUEUE_POP_SIZE`    | `10`    | Batch size when claiming tasks. Larger = fewer DB round-trips, more latency per pickup.        |
| `TASK_PROCESSOR_SLEEP_INTERVAL_MS` | `500`   | Poll interval between work checks (milliseconds). Lower = lower task latency but more DB load. |
| `TASK_PROCESSOR_GRACE_PERIOD_MS`   | `20000` | How long a task can run before being considered abandoned and retried.                         |

### Database connection lifetime

| Variable                       | Default | What it controls                                                                                                                    |
| ------------------------------ | ------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `DJANGO_DB_CONN_MAX_AGE`       | `60`    | Persistent connection lifetime in seconds. Higher = fewer reconnects, more idle connections held open against `max_connections`.    |
| `DJANGO_DB_CONN_HEALTH_CHECKS` | `false` | Validate each persistent connection before use. Slight overhead per request; useful if your DB occasionally drops idle connections. |

## Offloading analytics

SDK analytics generates write traffic on the main database. At Large and above, these writes compete with workload
tables for IOPS. Options:

| Option                                                                             | Effect                                                                                                                                  |
| ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `ANALYTICS_DATABASE_URL` (or `DJANGO_DB_NAME_ANALYTICS` + matching `_HOST` / etc.) | Sends analytics writes to a separate PostgreSQL database. Removes write contention from the main DB.                                    |
| `INFLUXDB_URL` + `INFLUXDB_TOKEN` + `INFLUXDB_BUCKET` + `INFLUXDB_ORG`             | Sends analytics to InfluxDB instead of PostgreSQL. Best for very high SDK analytics throughput.                                         |
| `RAW_ANALYTICS_DATA_RETENTION_DAYS` (default `30`)                                 | Reduce to shrink the raw analytics table size. Bucketed aggregates have their own retention (`BUCKETED_ANALYTICS_DATA_RETENTION_DAYS`). |

At Extra-Large, also consider running the task processor on its own database (`TASK_PROCESSOR_DATABASE_URL`). Its
recurring-task queries are a steady background load that needn't share IOPS with the workload writer.

## Metrics to monitor

Set alerts on these. The thresholds work as starting points; tighten or relax based on your error-budget and customer
SLOs.

| Layer                              | Metric                        | What to watch                                                                                                                                                             |
| ---------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **API**                            | CPU utilisation               | Sustained > 80% for more than 5% of any 30-day window means you're at capacity.                                                                                           |
| **API**                            | Memory utilisation            | Peak > 70% typically indicates a payload-size or worker-count tuning issue, not a sizing issue.                                                                           |
| **API**                            | p99 request latency           | Sustained > 1 second (excluding SSE long-poll endpoints) suggests gunicorn worker contention or slow downstream.                                                          |
| **Database**                       | CPU utilisation               | Peak > 70% means you should scale the database tier. First check whether enabling cache fixes it.                                                                         |
| **Database**                       | Provisioned IOPS              | Sustained > 80% of your provisioned IOPS = silent throttling. Bump the storage tier (not the CPU SKU).                                                                    |
| **Database**                       | Active connections            | > 70% of `max_connections` = add a connection pool (PgBouncer / RDS Proxy / Cloud SQL Auth Proxy).                                                                        |
| **Database**                       | Freeable memory               | < 5% of instance RAM at peak = memory-bound; bump the instance class.                                                                                                     |
| **Load balancer**                  | 5xx response rate             | > 0.1% of requests over a 1-hour window is worth investigating. Separate target-side from LB-side errors.                                                                 |
| **Load balancer**                  | Request count by status class | Watch the 2xx / 4xx / 5xx ratio for sudden shifts that aren't backed by traffic changes.                                                                                  |
| **Burstable DB credits** (if used) | Credit balance min            | If your instance class is burstable (AWS t-class, Azure B-series, GCP shared-core) and credits regularly hit 0, you're silently throttled. Move to a non-burstable class. |

## Scaling decision tree

When a metric crosses its threshold, follow the action below before reaching for a bigger SKU.

| Symptom                                                                | First action                                                                                      | If that doesn't help                                                  |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| API CPU sustained > 80%                                                | Increase worker count by 50% (or bump `HorizontalPodAutoscaler` min)                              | Move to next API tier                                                 |
| API memory > 70%                                                       | Increase gunicorn worker count per pod, or bump pod memory if your response payloads are large    | Trim segment / trait payloads. Large responses inflate worker memory. |
| Many 5xx at the load balancer with no corresponding target-side errors | Likely gunicorn worker exhaustion. Raise worker count + timeout per pod.                          | Investigate response payload size and segment / trait fan-out         |
| p99 latency > 1 s                                                      | Check gunicorn worker timeout vs payload size; check database CPU + IOPS                          | Move to next tier on whichever layer is bottlenecked                  |
| Database CPU > 70% peak                                                | **Turn on `CACHE_ENVIRONMENT_DOCUMENT_SECONDS=60`** if it isn't already. Often drops load by 10×. | Move to next database tier                                            |
| Database IOPS > 80% provisioned                                        | Bump storage tier / provisioned IOPS, not the CPU SKU                                             | Move to next database tier                                            |
| Burstable database credit min = 0                                      | Move to a non-burstable instance with the same vCPU / RAM                                         | n/a                                                                   |
| Database connections > 70% `max_connections`                           | Add a connection pool (PgBouncer / RDS Proxy / Cloud SQL Auth Proxy)                              | Bump `max_connections` alongside RAM                                  |
| SDK polling rate too high for current tier                             | Enable env-document cache, or raise SDK polling interval                                          | Move to next database tier                                            |

## What not to do

-   **Don't run Medium+ without env-document caching.** `CACHE_ENVIRONMENT_DOCUMENT_SECONDS` defaults to `0`. Turning it
    on drops database load ~10× for Pattern B traffic.
-   **Don't use burstable database classes at Medium+.** AWS `t3` / `t4g`, Azure B-series, Google Cloud shared-core.
    They mask sizing problems until CPU credits hit zero, then throttle silently.
-   **Don't size the database by HTTP RPS alone.** A Pattern B deployment at 2 RPS can produce more database load than a
    Pattern A deployment at 100 RPS.
-   **Don't ignore response payload size.** Pattern A responses with many segments / traits can reach tens of kilobytes.
    Large payloads exhaust gunicorn workers and cause LB-level 5xx. Trim payloads or raise gunicorn worker count +
    timeout.
-   **Don't oversize the task processor.** 1 vCPU / 2 GB handles every tier; two replicas for redundancy.

## Geographic deployments

Most Flagsmith deployments operate in a single region. If you need to serve users across regions with lower latency or
stricter data-residency requirements, there are two patterns to consider:

-   **[Flagsmith Edge Proxy](/performance/edge-proxy).** Cache flag evaluations closer to end users without operating a
    full second Flagsmith deployment. Best when you have many edge locations and a single source-of-truth Flagsmith.
-   **Separate Flagsmith deployment per region.** Strongest isolation, simplest operational model per region, but trades
    off central control of flags / segments.

Detailed geographic-expansion guidance is beyond the scope of this page. If you're planning a multi-region deployment,
please contact the Flagsmith team so we can validate the trade-offs against your specific requirements.
