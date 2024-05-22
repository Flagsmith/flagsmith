---
sidebar_label: Edge Proxy
title: Edge Proxy
sidebar_position: 25
---

## Configuration

The Edge Proxy can be configured using a json configuration file (named `config.json` here).

You can set the following configuration in `config.json` to control the behaviour of the Edge Proxy:

### `environment_key_pairs`

An array of environment key pair objects:

```json
"environment_key_pairs": [{
  "server_side_key": "your_server_side_key",
  "client_side_key": "your_client_side_environment_key"
}]
```

### `api_poll_frequency`

:::note

This setting is optional.

:::

Control how often the Edge Proxy is going to ping the server for changes, in seconds:

```json
"api_poll_frequency": 30
```

Defaults to `10`.

### `api_poll_timeout`

:::note

This setting is optional.

:::

Specify the request timeout when trying to retrieve new changes, in seconds:

```json
"api_poll_timeout": 1
```

Defaults to `5`.

### `api_url`

:::note

This setting is optional.

:::

Set if you are running a self hosted version of Flagsmith:

```json
"api_url": "https://my-flagsmith.domain.com/api/v1"
```

If not set, defaults to Flagsmith's Edge API.

### `allow_origins`

:::note

This setting is optional.

:::

Set a value for the `Access-Control-Allow-Origin` header.

```json
"allow_origins": "https://my-flagsmith.domain.com"
```

If not set, defaults to `*`.

### `endpoint_caches`

:::note

This setting is optional.

:::

Enable a LRU cache per endpoint.

Optionally, specify the LRU cache size with `cache_max_size` (defaults to 128):

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

### `logging.log_level`

:::note

This setting is optional.

:::

Choose a logging level from `"CRITICAL"`, `"ERROR"`, `"WARNING"`, `"INFO"`, `"DEBUG"`. Defaults to `"INFO"`.

```json
"logging": {"log_level": "DEBUG"}
```

### `logging.log_format`

:::note

This setting is optional.

:::

Choose a logging forman between `"generic"` and `"json"`. Defaults to `"generic"`.

```json
"logging": {"log_format": "json"}
```

### `logging.log_event_field_name`

:::note

This setting is optional.

:::

Set a name used for human-readable log entry field when logging events in JSON. Defaults to `"message"`.

```json
"logging": {"log_event_field_name": "event"}
```

### `config.json` example

Here's an example of a minimal working Edge Proxy configuration:

```json
{
 "environment_key_pairs": [
  {
   "server_side_key": "your_server_side_environment_key",
   "client_side_key": "your_client_side_environment_key"
  }
 ],
 "api_poll_frequency": 10,
 "api_url": "https://api.flagsmith.com/api/v1"
}
```

### Environment Variables

You can configure the Edge Proxy with the following Environment Variables:

- `WEB_CONCURRENCY` The number of [Uvicorn](https://www.uvicorn.org/) workers. Defaults to `1`. Set to the number of
  available CPU cores.

## Running the Edge Proxy

The Edge Proxy runs as a docker container. It is currently available at the
[Docker Hub](https://hub.docker.com/repository/docker/flagsmith/edge-proxy).

### With docker run

```bash
# Download the Docker Image
docker pull flagsmith/edge-proxy

# Run it
docker run \
    -v /<path-to-local>/config.json:/app/config.json \
    -p 8000:8000 \
    flagsmith/edge-proxy:latest
```

### With docker compose

```yml
version: '3.9'
services:
 edge_proxy:
  image: flagsmith/edge-proxy:latest
  volumes:
   - type: bind
     source: ./config.json
     target: /app/config.json
  ports:
   - target: 8000
   - published: 8000
```

The Proxy is now running and available on port 8000.

## Consuming the Edge Proxy

The Edge Proxy provides an identical set of API methods as our Core API. You need to point your SDK to the Edge Proxy
domain name and you're good to go. For example, lets say you had your proxy running locally as per the instructions
above:

```bash
curl "http://localhost:8000/api/v1/flags" -H "x-environment-key: 95DybY5oJoRNhxPZYLrxk4" | jq

[
    {
        "enabled": true,
        "feature_state_value": 5454,
        "feature": {
            "name": "feature_1",
            "id": 2,
            "type": "MULTIVARIATE"
        }
    },
    {
        "enabled": true,
        "feature_state_value": "some_value",
        "feature": {
            "name": "feature_2",
            "id": 9,
            "type": "STANDARD"
        }
    },
]
```

## Monitoring

There are 2 health check endpoints for the Edge Proxy.

### SDK Proxy Health Check

When making a request to `/proxy/health` the proxy will respond with a HTTP `200` and `{"status": "ok"}`. You can point
your orchestration health checks to this endpoint. This endpoint checks that the
[Environment Document](/clients/overview#the-environment-document) is not stale, and that the proxy is serving SDK
requests.

### Realtime Flags/Server Sent Events Health Check

If you are using the Proxy to power Server Sent Events for realtime flag updates. When making a request to `/sse/health`
the proxy will respond with a HTTP `200` and `{"status": "ok"}`.

## Architecture

The standard Flagsmith architecture:

![Image](/img/edge-proxy-existing.svg)

With the proxy added to the mix:

![Image](/img/edge-proxy-proxy.svg)
