---
sidebar_label: Edge Proxy
title: Edge Proxy
sidebar_position: 3
---

The [Edge Proxy](/performance/edge-proxy) runs as a
[Docker container](https://hub.docker.com/repository/docker/flagsmith/edge-proxy) with no external dependencies. It
connects to the Flagsmith API to download environment documents, and your Flagsmith client applications connect to it
using [remote flag evaluation](/integrating-with-flagsmith/sdks#remote-evaluation).

The examples below assume you have a configuration file located at `./config.json`. Your Flagsmith client applications
can then consume the Edge Proxy by setting their API URL to `http://localhost:8000/api/v1/`.

<details>
<summary>Docker CLI</summary>
```
docker run \
    -v ./config.json:/app/config.json \
    -p 8000:8000 \
    flagsmith/edge-proxy:latest
```
</details>

<details>
<summary>Docker Compose</summary>
```yaml title="compose.yaml"
services:
 edge_proxy:
  image: flagsmith/edge-proxy:latest
  volumes:
   - type: bind
     source: ./config.json
     target: /app/config.json
  ports:
   - '8000:8000'
```
</details>

## Configuration

The Edge Proxy can be configured with any combination of:

- Environment variables.
- A JSON configuration file, by default located at `/app/config.json` in the Edge Proxy container.

Environment variables take priority over their corresponding options defined in the configuration file.

Environment variable names are case-insensitive, and are processed using
[Pydantic](https://docs.pydantic.dev/2.7/concepts/pydantic_settings/#environment-variable-names).

### Example configuration

<details>

<summary>Configuration file</summary>

```json title="/app/config.json"
{
 "environment_key_pairs": [
  {
   "server_side_key": "ser.your_server_side_key_1",
   "client_side_key": "your_client_side_key_1"
  }
 ],
 "api_poll_frequency_seconds": 5,
 "logging": {
  "log_level": "DEBUG",
  "log_format": "json"
 }
}
```

</details>

<details>

<summary>Environment variables</summary>

```ruby
ENVIRONMENT_KEY_PAIRS='[{"server_side_key":"ser.your_server_side_key_1","client_side_key":"your_client_side_key_1"}]'
API_POLL_FREQUENCY_SECONDS=5
LOGGING='{"log_level":"DEBUG","log_format":"json"}'
```

</details>

### Basic settings

#### `environment_key_pairs`

Specifies which environments to poll environment documents for. Each environment requires a server-side key and its
corresponding client-side key.

```json
"environment_key_pairs": [{
  "server_side_key": "ser.your_server_side_key",
  "client_side_key": "your_client_side_environment_key"
}]
```

#### `api_url`

If you are self-hosting Flagsmith, set this to your API URL:

```json
"api_url": "https://flagsmith.example.com/api/v1"
```

#### `api_poll_frequency_seconds`

How often to poll the Flagsmith API for changes, in seconds. Defaults to 10.

```json
"api_poll_frequency_seconds": 30
```

#### `api_poll_timeout_seconds`

The request timeout when trying to retrieve new changes, in seconds. Defaults to 5.

```json
"api_poll_timeout_seconds": 1
```

#### `allow_origins`

Set a value for the `Access-Control-Allow-Origin` header. Defaults to `*`.

```json
"allow_origins": "https://www.example.com"
```

### Endpoint caches

#### `endpoint_caches`

Enables a LRU cache per endpoint.

Optionally, specify the LRU cache size with `cache_max_size`. Defaults to 128.

```json
"endpoint_caches": {
  "flags": {
    "use_cache": false
  },
  "identities": {
    "use_cache": true,
    "cache_max_size": 1000,
  }
}
```

### Server settings

#### `server.proxy_headers`

When set to `true`, the Edge Proxy will use the `X-Forwarded-For` and `X-Forwarded-Proto` HTTP headers to determine
client IP addresses. This is useful if the Edge Proxy is running behind a reverse proxy, and you want the
[access logs](#loggingoverride) to show the real IP addresses of your clients.

By default, only the loopback address is trusted. This can be changed with the
[`FORWARDED_ALLOW_IPS` environment variable](#environment-variables).

```json
"server": {
  "proxy_headers": true
}
```

```
SERVER_PROXY_HEADERS=true
```

### Logging

#### `logging.log_level`

Choose a logging level from `"CRITICAL"`, `"ERROR"`, `"WARNING"`, `"INFO"`, `"DEBUG"`. Defaults to `"INFO"`.

```json
"logging": {"log_level": "DEBUG"}
```

#### `logging.log_format`

Choose a logging format between `"generic"` and `"json"`. Defaults to `"generic"`.

```json
"logging": {"log_format": "json"}
```

#### `logging.log_event_field_name`

Set a name used for human-readable log entry field when logging events in JSON. Defaults to `"message"`.

```json
"logging": {"log_event_field_name": "event"}
```

#### `logging.colour`

Added in [2.13.0](https://github.com/Flagsmith/edge-proxy/releases/tag/v2.13.0).

Set to `false` to disable coloured output. Useful when outputting the log to a file.

#### `logging.override`

Added in [2.13.0](https://github.com/Flagsmith/edge-proxy/releases/tag/v2.13.0).

Accepts
[Python-compatible logging settings](https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema)
in JSON format. You're able to define custom formatters, handlers and logger configurations. For example, to log
everything a file, one can set up own file handler and assign it to the root logger:

```json
"logging": {
  "override": {
      "handlers": {
          "file": {
              "level": "INFO",
              "class": "logging.FileHandler",
              "filename": "edge-proxy.log",
              "formatter": "json"
          }
      },
      "loggers": {
          "": {
              "handlers": ["file"],
              "level": "INFO",
              "propagate": true
          }
      }
  }
}
```

Or, log access logs to file in generic format while logging everything else to stdout in JSON:

```json
"logging": {
  "override": {
      "handlers": {
          "file": {
              "level": "INFO",
              "class": "logging.FileHandler",
              "filename": "edge-proxy.log",
              "formatter": "generic"
          }
      },
      "loggers": {
          "": {
              "handlers": ["default"],
              "level": "INFO"
          },
          "uvicorn.access": {
              "handlers": ["file"],
              "level": "INFO",
              "propagate": false
          }
      }
  }
}
```

When adding logger configurations, you can use the `"default"` handler which writes to stdout and uses formatter
specified by the [`"logging.log_format"`](#logginglog_format) setting.

### Health checks

The Edge Proxy exposes two health check endpoints:

- `/proxy/health/liveness`: Always responds with a 200 status code. Use this health check to determine if the Edge Proxy
  is alive and able to respond to requests.
- `/proxy/health/readiness`: Responds with a 200 status if the Edge Proxy was able to fetch all its configured
  environment documents within a configurable grace period. This allows the Edge Proxy to continue reporting as healthy
  even if the Flagsmith API is temporarily unavailable. This health check is also available at `/proxy/health`.

You should point your orchestration health checks to these endpoints.

#### `health_check.environment_update_grace_period_seconds`

Default: `30`.

The number of seconds to allow per environment key pair before the environment data stored by the Edge Proxy is
considered stale.

When set to `null`, cached environment documents are never considered stale, and health checks will succeed if all
environments were successfully fetched at some point since the Edge Proxy started.

The effective grace period depends on how many environments the Edge Proxy is configured to serve. It can be calculated
using the following pseudo-Python code:

```python
total_grace_period_seconds = api_poll_frequency + (environment_update_grace_period_seconds * len(environment_key_pairs))
if last_updated_all_environments_at < datetime.now() - timedelta(seconds=total_grace_period_seconds):
    # Data is stale
    return 500
# Data is not stale
return 200
```

### Environment variables

Some Edge Proxy settings can only be set using environment variables:

- `WEB_CONCURRENCY` The number of [Uvicorn](https://www.uvicorn.org/) workers. Defaults to `1`, which is
  [recommended when running multiple Edge Proxy containers behind a load balancer](https://fastapi.tiangolo.com/deployment/docker/#one-load-balancer-multiple-worker-containers).
  If running on a single node, set this
  [based on your number of CPU cores and threads](https://docs.gunicorn.org/en/latest/design.html#how-many-workers).
- `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`: Configure an HTTP proxy for the Edge Proxy's outgoing requests,
  with `NO_PROXY` exempting matching hosts. [Learn more](https://www.python-httpx.org/environment_variables)
- `FORWARDED_ALLOW_IPS`: Which IPs to trust for determining client IP addresses when using the `proxy_headers` option.
  For more details, see the [Uvicorn documentation](https://www.uvicorn.org/settings/#http).

## Identity overrides

Identity overrides defined in the dashboard are evaluated by the Edge Proxy. They are embedded in the environment
document the proxy fetches from the Flagsmith API, and applied during local evaluation by the Flagsmith engine.

For overrides to flow through to the Edge Proxy, **Environment Settings → SDK Settings → Use identity overrides in
local evaluation** must be enabled. This is the default for new environments.

:::warning Edge Proxy version

Deleting an identity override in the dashboard only propagates to the Edge Proxy on
[v2.21.1](https://github.com/Flagsmith/edge-proxy/releases/tag/v2.21.1) and newer. Earlier versions kept the deleted
override in their cached environment document, so the proxy returned the old overridden value. Pin to `v2.21.1` or
later, or use `:latest`, to pick up override deletions.

:::

When a **request** matches both an identity override and a segment override, the identity override takes precedence —
this matches the behaviour of
[Local Evaluation Mode](/integrating-with-flagsmith/integration-overview#local-evaluation-mode).

## Troubleshooting

### 401 Unauthorized from the Edge Proxy

The Edge Proxy returns `401 {"status": "unauthorized", "message": "unknown key ..."}` when the `X-Environment-Key`
header sent by your client does not match any key configured in [`environment_key_pairs`](#environment_key_pairs).

Check that:

- Your client is using the **client-side** environment key, not the server-side key.
- The client-side key in your SDK exactly matches the `client_side_key` in the proxy's configuration.
- If you rotated keys in the dashboard, the proxy configuration was updated and the proxy was restarted.

### 403 Forbidden in Edge Proxy logs

A 403 in the proxy's `error_fetching_document` log line comes from the **upstream Flagsmith API** rejecting the
configured server-side key when the proxy polls for an environment document. The proxy itself does not return 403; it
surfaces the upstream error and keeps serving the last cached document if one exists.

Diagnose in this order:

1. **Key prefix and presence.** `server_side_key` values must be non-empty and start with `ser.`. The proxy validates
   this at startup and refuses to launch otherwise — a blank or whitespace-only server key fails the same check.
2. **Key type.** Confirm the key was created as **Server-side Environment Key** in **Environment settings → SDK Keys**.
   Client-side keys cannot fetch environment documents.
3. **Key freshness.** If the key was rotated or deleted in the dashboard, the proxy's cached value is now invalid.
4. **`api_url`.** When self-hosting, [`api_url`](#api_url) must point at your Flagsmith API (e.g.
   `https://flagsmith.example.com/api/v1`). Pointing a self-hosted proxy at `edge.api.flagsmith.com` will 403 because
   the key does not exist on Flagsmith's hosted Edge.

### Restart loops in ECS, Kubernetes, or other orchestrators

The most common cause is the orchestrator's readiness probe firing before the proxy has fetched its first environment
document, or fluctuating to unhealthy whenever the upstream API is briefly slow.

- Point readiness probes at [`/proxy/health/readiness`](#health-checks) and liveness probes at `/proxy/health/liveness`.
  **Do not** point liveness at readiness — a transient upstream outage will then kill the container instead of letting
  it serve cached documents.
- Increase the readiness probe's `initialDelaySeconds` (Kubernetes) or `startPeriod` (ECS) to comfortably exceed the
  time it takes to fetch all configured environment documents on a cold start.
- If you serve many environments from a single proxy, raise
  [`health_check.environment_update_grace_period_seconds`](#health_checkenvironment_update_grace_period_seconds) or set
  it to `null` to keep the proxy healthy when the upstream API is intermittently unavailable.

### Stale flags after a dashboard change

The proxy serves cached environment documents and only re-fetches every
[`api_poll_frequency_seconds`](#api_poll_frequency_seconds) (default 10s). It also uses `If-Modified-Since` and will log
a 304 when the upstream document hasn't changed.

To diagnose:

- Set [`logging.log_level`](#logginglog_level) to `DEBUG` and watch for `environment_updated` log events after you
  publish a change.
- Verify the proxy can reach the upstream API. A 5xx, timeout, or 403 from the upstream API will leave the proxy serving
  the last successfully-fetched document.
- For very fast propagation requirements, lower `api_poll_frequency_seconds`, but be aware this increases load on the
  upstream API proportionally.

### Identity-based evaluation returns the wrong value

If your client is hitting the proxy and the result differs from a direct API call:

- Confirm you are sending the full set of traits on every request. The proxy is stateless and does not persist traits
  between calls — see [Managing Traits](/performance/edge-proxy#managing-traits).
- If the result was correct before and is now stale after deleting an identity override, upgrade to Edge Proxy v2.21.1
  or newer (see [Identity overrides](#identity-overrides)).
- Disable [endpoint caches](#endpoint_caches) temporarily to rule out a cached response.

## Production deployment

### Behind a reverse proxy or load balancer

- Set [`server.proxy_headers`](#serverproxy_headers) to `true` so access logs record the real client IP.
- Use the [`FORWARDED_ALLOW_IPS`](#environment-variables) environment variable to list the load balancer's IPs.
- Run multiple Edge Proxy containers behind the load balancer with `WEB_CONCURRENCY=1` per container, as recommended by
  FastAPI. The proxy is stateless, so any instance can serve any request.
- Health-check path on the load balancer should be `/proxy/health/readiness`.

### ECS / Fargate

- Map container port `8000` and front the service with an ALB or NLB.
- Set the ECS health check `command` or the target group health check path to `/proxy/health/readiness`.
- Use `startPeriod` on the ECS health check (typically 30–60s) so the task is not killed during initial document
  fetches.
- The task needs outbound internet (or VPC routing) to reach the Flagsmith API. If you use a forward proxy, set
  `HTTPS_PROXY` and `NO_PROXY` on the task definition.
- Mount your `config.json` as a file (for example, via a sidecar that pulls from S3 or AWS Secrets Manager) rather than
  baking server-side keys into the image.

### Kubernetes

The Edge Proxy is a stateless Deployment. There is no official Helm chart at the time of writing; a minimal manifest
looks like this:

```yaml title="edge-proxy.yaml"
apiVersion: apps/v1
kind: Deployment
metadata:
 name: edge-proxy
spec:
 replicas: 2
 selector:
  matchLabels: { app: edge-proxy }
 template:
  metadata:
   labels: { app: edge-proxy }
  spec:
   containers:
    - name: edge-proxy
      image: flagsmith/edge-proxy:latest
      ports:
       - containerPort: 8000
      readinessProbe:
       httpGet: { path: /proxy/health/readiness, port: 8000 }
       initialDelaySeconds: 10
      livenessProbe:
       httpGet: { path: /proxy/health/liveness, port: 8000 }
      volumeMounts:
       - name: config
         mountPath: /app/config.json
         subPath: config.json
   volumes:
    - name: config
      secret:
       secretName: edge-proxy-config
```

Store `config.json` in a `Secret` (it contains server-side keys). Scale with `replicas` or an HPA on CPU.

### Managing configuration in CI/CD

`config.json` contains server-side environment keys and should be treated as a secret:

- Keep the file out of version control. Render it at deploy time from your secrets store (Vault, AWS Secrets Manager,
  GCP Secret Manager, Kubernetes `Secret`, etc.).
- If a static-analysis tool flags committed keys, rotate them in the dashboard immediately and move the new keys into
  your secrets store.

## Architecture and scaling

The Edge Proxy is stateless: each instance independently polls the Flagsmith API and serves cached environment
documents, so it scales linearly behind a load balancer.

When sizing a fleet:

- Each proxy instance polls the upstream API once per environment per
  [`api_poll_frequency_seconds`](#api_poll_frequency_seconds), so adding instances multiplies the polling load on the
  upstream API.
- Enable [`endpoint_caches`](#endpoint_caches) for `flags` and `identities` if you have many repeating requests. Caches
  are scoped per-process and cleared whenever the environment document changes, so they cannot serve stale data after a
  dashboard change.
- The proxy is CPU-bound on `flags` and `identities` (engine evaluation) and bandwidth-bound on `environment-document`
  (large response body). Scale on CPU for the first two, and on outbound network for the third.

### Reference throughput per instance

The numbers below come from internal benchmarks of `flagsmith/edge-proxy:2.21.2` running as a single-worker container on
a 1 vCPU / 2 GB AWS Fargate task, with endpoint caches **disabled** (worst case — every request runs a full evaluation).
Use them as starting-point sizing; real throughput depends on project shape, segment complexity, and trait counts.

Project profile: 50 features, 15 segments, every feature overridden by every segment (750 segment overrides total), each
segment matching on 15 trait conditions. The "Concurrency at peak" column is the client concurrency level at which the
peak RPS was observed — past that point, extra concurrency adds queueing without raising throughput.

| Endpoint                           | Peak RPS | Concurrency at peak |
| ---------------------------------- | -------: | ------------------: |
| `POST /api/v1/identities/`         |      ~72 |                  25 |
| `GET /api/v1/flags/`               |      ~63 |                  10 |
| `GET /api/v1/environment-document` |     ~570 |                  25 |

To raise per-instance throughput, run more containers behind the load balancer with `WEB_CONCURRENCY=1` per container,
or increase `WEB_CONCURRENCY` and the container's CPU allocation when running a single container per node.
