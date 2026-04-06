---
title: OpenTelemetry
description: Exporting traces and structured logs from Flagsmith using OpenTelemetry.
---

Flagsmith supports exporting distributed traces and structured logs over
[OTLP](https://opentelemetry.io/docs/specs/otel/protocol/), the OpenTelemetry Protocol. This lets you send observability
data to any OTLP-compatible backend (e.g. SigNoz, Grafana Tempo, Jaeger, Datadog) without vendor lock-in.

OTel instrumentation is opt-in and has no runtime overhead when disabled.

## Configuration

Set `OTEL_EXPORTER_OTLP_ENDPOINT` to the base OTLP/HTTP URL of your collector (e.g. `http://collector:4318`) to enable
OTel export. When unset, no OTel code is loaded and there is no runtime overhead.

Standard `OTEL_*` environment variables are also respected by the underlying OTel SDK. For example:

- `OTEL_SERVICE_NAME` — overrides the `service.name` resource attribute (defaults to `flagsmith-api` or
  `flagsmith-task-processor`).
- `OTEL_RESOURCE_ATTRIBUTES` — adds custom resource attributes.
- `OTEL_EXPORTER_OTLP_HEADERS` — sets authentication headers for the OTLP exporter.

### Example: Docker Compose

```yaml
api:
 environment:
  OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4318
```

## Traces

When enabled, Flagsmith produces distributed traces for every HTTP request.

### What gets instrumented

| Layer            | Instrumentation               | Span example                               |
| ---------------- | ----------------------------- | ------------------------------------------ |
| HTTP requests    | Django auto-instrumentation   | `GET /api/v1/organisations/{pk}/`          |
| Database queries | psycopg2 auto-instrumentation | `SELECT` (with full SQL in `db.statement`) |
| Redis commands   | Redis auto-instrumentation    | `GET` / `SET` / `EVAL`                     |

Each HTTP request creates a root server span with child client spans for every database query and Redis command
executed during the request.

### Span naming

HTTP spans are named `{METHOD} {route_template}`, where the route template matches the path format used in the OpenAPI
spec:

- `POST /api/v1/environments/{environment_api_key}/featurestates/`
- `GET /api/v1/projects/{project_pk}/features/`

The `http.route` attribute is set to the same normalised template.

### Trace context propagation

Flagsmith propagates [W3C TraceContext](https://www.w3.org/TR/trace-context/) and
[W3C Baggage](https://www.w3.org/TR/baggage/) headers. If an upstream service sends a `traceparent` header, Flagsmith's
spans join the existing trace. Baggage entries are forwarded into structlog attributes (see below).

### SQL commenter

The psycopg2 instrumentor has [SQL commenter](https://google.github.io/sqlcommenter/) enabled. This appends trace
context as a SQL comment to every query sent to PostgreSQL:

```sql
SELECT "organisations_organisation"."id" FROM "organisations_organisation"
/*traceparent='00-abc123...-def456...-01'*/
```

This allows correlating slow queries in PostgreSQL logs or `pg_stat_statements` back to the originating trace, without
any changes to PostgreSQL configuration.

### Excluding paths

Health check endpoints and other high-frequency, low-value paths can be excluded from tracing:

```
OTEL_TRACING_EXCLUDED_URL_PATHS=health/liveness,health/readiness
```

Excluded paths produce no spans at all.

## Structured logs

Flagsmith uses [structlog](https://www.structlog.org/) for application logging. When OTel is enabled, structlog events
are exported as OTLP log records. The `flagsmith.event` attribute duplicates the event name for backends that don't surface OTel's `EventName` field.

### Span events

When a structlog event is emitted inside an active span (e.g. during an HTTP request), it is also attached as a
[span event](https://opentelemetry.io/docs/concepts/signals/traces/#span-events) with the same name and attributes. This
makes application log events visible in trace detail views without requiring separate log correlation.

### Console output

When OTel is enabled, structlog events also include `trace_id` and `span_id` fields in their console/JSON output when an
active span exists:

```
2025-03-31T15:34:32Z [info] list_organisations [organisations] trace_id=aabb... span_id=ccdd... user_id=1
```
