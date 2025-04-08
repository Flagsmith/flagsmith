---
sidebar_label: Edge Proxy
title: Edge Proxy
sidebar_position: 25
---

The [Edge Proxy](/advanced-use/edge-proxy) runs as a
[Docker container](https://hub.docker.com/repository/docker/flagsmith/edge-proxy) with no external dependencies.
It connects to the Flagsmith API to download environment documents, and your Flagsmith client applications connect to it
using [remote flag evaluation](/clients/#remote-evaluation).

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
[access logs](#logging.override) to show the real IP addresses of your clients.

By default, only the loopback address is trusted. This can be changed with the [`FORWARDED_ALLOW_IPS` environment
variable](#environment-variables).

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

* `/proxy/health/liveness`: Always responds with a 200 status code. Use this health check to determine if the Edge
  Proxy is alive and able to respond to requests.
* `/proxy/health/readiness`: Responds with a 200 status if the Edge Proxy was able to fetch all its configured
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
  If running on a single node, set this [based on your number of CPU cores and threads](https://docs.gunicorn.org/en/latest/design.html#how-many-workers).
- `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`: These variables let you configure an HTTP proxy that the
  Edge Proxy should use for all its outgoing HTTP requests.
  [Learn more](https://www.python-httpx.org/environment_variables)
- `FORWARDED_ALLOW_IPS`: Which IPs to trust for determining client IP addresses when using the `proxy_headers` option.
  For more details, see the [Uvicorn documentation](https://www.uvicorn.org/settings/#http).
