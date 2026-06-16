---
sidebar_label: MCP Server
title: MCP Server
sidebar_position: 4
description: Run the Flagsmith MCP Server as part of your self-hosted deployment.
---

The [Flagsmith MCP Server](/integrating-with-flagsmith/mcp-server) gives AI assistants and agents access to the
Flagsmith Admin API through the [Model Context Protocol](https://modelcontextprotocol.io). On Flagsmith SaaS it is
hosted for you at `https://mcp.flagsmith.com`. When you self-host Flagsmith, you run the server yourself as an
additional container alongside your API.

It runs as a [Docker container](https://hub.docker.com/r/flagsmith/flagsmith-mcp) with no dependencies of its own: it
talks to your Flagsmith API over HTTP, and MCP clients connect to it over
[Streamable HTTP](https://modelcontextprotocol.io/specification/basic/transports#streamable-http).

## Running the server

Point the server at your Flagsmith API with `FLAGSMITH_API_URL` and expose its HTTP port. The examples below assume your
API is reachable at `https://flagsmith.example.com` and serve the MCP endpoint on port 8000.

<details>
<summary>Docker CLI</summary>
```
docker run \
    -e FLAGSMITH_API_URL=https://flagsmith.example.com \
    -e MCP_SERVER_URL=https://mcp.flagsmith.example.com \
    -p 8000:8000 \
    flagsmith/flagsmith-mcp:latest
```
</details>

<details>
<summary>Docker Compose</summary>
```yaml title="compose.yaml"
services:
 mcp:
  image: flagsmith/flagsmith-mcp:latest
  environment:
   FLAGSMITH_API_URL: https://flagsmith.example.com
   MCP_SERVER_URL: https://mcp.flagsmith.example.com
  ports:
   - '8000:8000'
```
</details>

The server is reachable at `/mcp`, and also at the bare URL — a request to `/` is dispatched to the MCP endpoint, so
clients that drop the `/mcp` suffix still work. Browsers that open the bare URL are redirected to this documentation.

## Configuration

The server is configured entirely through environment variables.

| Variable                      | Default                     | Description                                                                                                                                                               |
| ----------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FLAGSMITH_API_URL`           | `https://api.flagsmith.com` | Base URL of the Flagsmith API the server proxies. Set this to your self-hosted API.                                                                                       |
| `MCP_SERVER_URL`              | `http://127.0.0.1:8000`     | Public base URL of this server, advertised in OAuth metadata. Set this to the externally reachable URL when running behind a proxy.                                       |
| `TRANSPORT`                   | `http`                      | MCP transport. Use `http` for a hosted server. `stdio` runs the server as a local subprocess and requires `FLAGSMITH_API_TOKEN`.                                          |
| `FASTMCP_HOST`                | `0.0.0.0`                   | Host the HTTP transport binds to.                                                                                                                                         |
| `FASTMCP_PORT`                | `8000`                      | Port the HTTP transport binds to.                                                                                                                                         |
| `FLAGSMITH_API_TOKEN`         | _(unset)_                   | A static [API key](/integrating-with-flagsmith/flagsmith-api-overview/admin-api/authentication) the server uses for every request. See [Authentication](#authentication). |
| `METRICS_PORT`                | _(unset)_                   | Serve [Prometheus metrics](/deployment-self-hosting/observability/metrics) on this port. Disabled when unset.                                                             |
| `LOG_LEVEL`                   | `INFO`                      | Log level for application loggers.                                                                                                                                        |
| `LOG_FORMAT`                  | `generic`                   | Log output format. Set to `json` for structured logs.                                                                                                                     |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | _(unset)_                   | [OpenTelemetry](/deployment-self-hosting/observability/opentelemetry) endpoint to export logs and traces to. Export is disabled when unset.                               |
| `OTEL_SERVICE_NAME`           | `flagsmith-mcp`             | Service name reported to OpenTelemetry.                                                                                                                                   |

## Authentication

The server forwards each client's credential to the Flagsmith API, so clients authenticate as themselves and inherit
their own permissions. There are three ways to authenticate, controlled by how you run the server.

### OAuth (interactive clients)

When you run the server over HTTP without setting `FLAGSMITH_API_TOKEN`, it advertises OAuth metadata pointing at your
Flagsmith API as the authorisation server. Interactive clients discover this automatically and complete a browser login
on first connection — no API keys to distribute. Set `MCP_SERVER_URL` to the externally reachable URL of the server so
the advertised metadata is correct behind a proxy.

OAuth requires a Flagsmith deployment that exposes the MCP authorisation-server endpoints. If yours does not, use an API
key instead.

### API key (non-interactive clients)

Clients can authenticate per request by sending an
[Organisation API key](/integrating-with-flagsmith/flagsmith-api-overview/admin-api/authentication) in the
`Authorization` header:

```
Authorization: Api-Key <your-api-key>
```

The server forwards this header to the Flagsmith API unchanged. This suits CI jobs and headless agents.

### Static API key (single shared credential)

Setting `FLAGSMITH_API_TOKEN` makes the server use that key for every request, regardless of which client connects. This
disables OAuth and is the only option for the `stdio` transport, which has no inbound request to forward a credential
from. Avoid it for shared HTTP deployments, since every client then acts with the same permissions.

## Connecting clients

Point your MCP client at your server's base URL instead of `https://mcp.flagsmith.com`. The
[MCP Server integration guide](/integrating-with-flagsmith/mcp-server#installing-in-your-client) has per-client
configuration for Claude Code, Cursor, VS Code, and others.

## Health check

The server exposes a `GET /health` endpoint that returns `200 OK`. The container also ships with a Docker `HEALTHCHECK`
that polls it, so orchestrators can detect readiness without extra configuration.

## Observability

The server emits [structured logs](/deployment-self-hosting/observability/events),
[Prometheus metrics](/deployment-self-hosting/observability/metrics) (when `METRICS_PORT` is set), and
[OpenTelemetry traces and logs](/deployment-self-hosting/observability/opentelemetry) (when
`OTEL_EXPORTER_OTLP_ENDPOINT` is set), spanning both the MCP server and the upstream Flagsmith API calls it makes.
