---
title: Deployment guide
sidebar_label: Deployment
sidebar_position: 30
---

## Redis

First, deploy a Redis-compatible store, such as [Valkey](https://valkey.io/). Many managed options for Redis-compatible
stores are offered by different cloud providers. Some examples:

- [Amazon ElastiCache (AWS)](https://aws.amazon.com/elasticache/features/)
- [Memorystore for Valkey (GCP)](https://cloud.google.com/memorystore/docs/valkey/product-overview)
- [Azure cache for Redis](https://azure.microsoft.com/en-us/products/cache)

Clustering Redis is recommended for high availability, but not required. All
[current Redis versions](https://redis.io/docs/latest/operate/rs/installing-upgrading/product-lifecycle/) are supported.

### Authentication

Redis must not require a password for the default user. Options for authentication will be added in the future.

## SSE service

Run the `flagsmith/sse` image, setting these environment variables:

| Variable name                   | Description                                                                                                                     | Default      |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| `SSE_AUTHENTICATION_TOKEN`      | Shared secret for authentication on the `/queue-change` endpoint                                                                | **Required** |
| `REDIS_HOST`                    | Hostname of the Redis load balancer                                                                                             | `localhost`  |
| `REDIS_PORT`                    | Port number to use when connecting to Redis                                                                                     | 6379         |
| `REDIS_SCAN_COUNT`              | Number of Redis keys to [`SCAN`](https://redis.io/docs/latest/commands/scan/) at once when updating the in-memory cache         | 500          |
| `CACHE_UPDATE_INTERVAL_SECONDS` | How long (in seconds) to wait between each `SCAN` to update the in-memory cache                                                 | 1            |
| `USE_CLUSTER_MODE`              | Whether to connect to Redis with [Cluster Mode](https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/) enabled | `False`      |
| `REDIS_USE_SSL`                 | Whether to connect to Redis with SSL                                                                                            | `False`      |
| `MAX_STREAM_AGE`                | How long (in seconds) to keep SSE connections alive for. If negative, connections are kept open indefinitely                    | 30           |
| `STREAM_DELAY`                  | How long (in seconds) to wait before checking the internal cache for updates                                                    | 1            |

The SSE service will expose its endpoints to `0.0.0.0:8000`.

## API and task processor

The Flagsmith API and task processor need to know about the SSE service. On both the API and task processor, set these
environment variables:

- `SSE_SERVER_BASE_URL` points to the SSE service load balancer. For example: `http://my-sse-service:8000`
- `SSE_AUTHENTICATION_TOKEN` can be set to any non-empty string, as long as the SSE service and task processor share the
  same value.

## Flagsmith configuration

Make sure the Flagsmith projects you are updating have real-time updates enabled. If not, no tasks will be queued when
its environments are updated.

Lastly, client applications should set their Flagsmith SDK's realtime endpoint URL to the load balancer for the SSE
service.

## Example: Docker Compose

The following Docker Compose file defines a simple Flagsmith deployment. The highlighted lines are required to support
real-time flag updates.

```yaml title="compose.yaml"
services:
 # highlight-start
 valkey:
  image: valkey/valkey:latest
  # highlight-end

  # highlight-start
 sse:
  image: flagsmith/sse:3.3.0
  environment:
   SSE_AUTHENTICATION_TOKEN: changeme
   REDIS_HOST: valkey
  depends_on:
   - valkey
 # highlight-end

 flagsmith:
  # highlight-start
  image: flagsmith/flagsmith-private-cloud:latest
  # highlight-end
  environment:
   # highlight-start
   SSE_AUTHENTICATION_TOKEN: changeme
   SSE_SERVER_BASE_URL: 'http://sse:8000'
   # highlight-end
   DATABASE_URL: postgresql://postgres:password@postgres:5432/flagsmith
   USE_POSTGRES_FOR_ANALYTICS: 'true'
   ENVIRONMENT: production
   DJANGO_ALLOWED_HOSTS: '*'
   ALLOW_ADMIN_INITIATION_VIA_CLI: 'true'
   FLAGSMITH_DOMAIN: 'localhost:8000'
   DJANGO_SECRET_KEY: secret
   ENABLE_ADMIN_ACCESS_USER_PASS: 'true'
   TASK_RUN_METHOD: TASK_PROCESSOR
  ports:
   - '8000:8000'
  depends_on:
   - postgres

 # The flagsmith_processor service is only needed if TASK_RUN_METHOD set to TASK_PROCESSOR
 # in the application environment
 flagsmith_processor:
  image: flagsmith/flagsmith:latest
  environment:
   # highlight-start
   SSE_AUTHENTICATION_TOKEN: changeme
   SSE_SERVER_BASE_URL: 'http://sse:8000'
   # highlight-end
   DATABASE_URL: postgresql://postgres:password@postgres:5432/flagsmith
   USE_POSTGRES_FOR_ANALYTICS: 'true'
  depends_on:
   - flagsmith
  command: run-task-processor

 postgres:
  image: postgres:15.5-alpine
  environment:
   POSTGRES_PASSWORD: password
   POSTGRES_DB: flagsmith
  container_name: flagsmith_postgres
  volumes:
   - pgdata:/var/lib/postgresql/data

volumes:
 pgdata:
```
