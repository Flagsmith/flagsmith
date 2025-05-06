---
title: Operations
sidebar_label: Operations
sidebar_position: 30
---

The Flagsmith API is always the primary source of flag data for client applications. Real-time flag updates, as the name
implies, are only a messaging channel for notifying client applications of any updates. These updates are control
messages, which do not have any flag data.

This document describes how to operate the real-time updates system for scale and reliability.

## Operational goals

The real-time updates system optimises for the following goals, listed from most to least important:

- Delivery reliability. All subscribers receive all their updates.
- Operational reliability. In normal circumstances, any part of the system can be replaced at any time while maintaining
  availability overall. Handle unexpected traffic and chaotic events gracefully and without involving humans.
- Deployment flexibility. Introduce as few dependencies as possible to minimise security and policy risks. Support
  deploying to as many environments as possible, in the cloud or on-premises.
- Scalability. Handle concurrent subscribers in the order of 100.000s with horizontal scaling.
- Speed. Deliver updates as quickly as possible.

## Scaling factors

The performance of the real-time updates system will depend mainly on:

- The latency and reliability of your clients' TCP connections
- How many clients are subscribed at the same time to each SSE instance
- How many clients are being notified by any environment updates
- How often environments with active subscribers are updated

## Availability

At least one SSE service instance and one Redis node are required for real-time updates to work. The SSE service will
reject subscriptions from client applications if Redis is unavailable.

Both Redis and the SSE service can be scaled horizontally to handle more concurrent subscribers and for reliability.

## Message deliverability

Clients that use SSE can only receive data and not send data. As such, they cannot acknowledge they have received an
update from the SSE service. Deliverability will be limited by the reliability of your clients' TCP connections. This is
a constraint of the current real-time implementation of all Flagsmith SDKs, which do not have a way to acknowledge
received messages.

When a client subscribes to real-time updates for an environment, the SSE service will immediately return the latest
update timestamp. This increases reliability in the event of reconnections and undetectable delivery failures.

The SSE service sends a keep-alive message to each subscriber every 15 seconds if nothing was sent. This is to prevent
load balancers, NAT gateways or other proxies from closing otherwise inactive connections.

## Latency

The goal is to minimise **end-to-end latency**, which is the time taken between the Flagsmith API acknowledging an
environment update, and a client getting notified of this update over SSE. Ignoring network delays, this will mainly
depend on:

- How often the [task processor](https://docs.flagsmith.com/deployment/configuration/task-processor) is polling the API
  for new tasks (by default 2 seconds)
- How long the "environment updated" tasks take to execute (varies on task processor and database load)
- How fast Redis can acknowledge the update (usually milliseconds)
- How fast the relevant SSE service instances can pull from Redis (by default every second)
- How often the SSE service checks the in-memory cache for updates for each subscriber (by default every second)
- Network delay between SSE service instances and client applications

## Storage

Redis stores a timestamp of when each environment was last updated. Each key is named `sse:ENVIRONMENT_ID`.

## Security

Subscribing to real-time updates via the SSE service does not require authentication. The SSE service allows all CORS
requests on all endpoints.

The task processor authenticates with the SSE service when publishing an update by using a shared secret. This secret is
configured using the `SSE_AUTHENTICATION_TOKEN` environment variable. For example:

```
curl -X POST -H "Authorization: Token $SSE_AUTHENTICATION_TOKEN" -H "Content-Type: application/json" -d' {"updated_at":"2023-01-12T18:06:42.028060"}' http://localhost:8088/sse/environments/abcxyz/queue-change
```

## Monitoring

Make sure you are [monitoring the task processor](/deployment/configuration/task-processor#monitoring), as the SSE
service depends on it.

The SSE service exposes a health check endpoint at `/health`, which can be used for liveness and readiness checks. It
responds with 200 if the SSE service can accept incoming connections and is connected to Redis by sending it a
[`PING` command](https://redis.io/docs/latest/commands/ping/).

## Metrics

TODO: The following is not yet implemented!

The SSE service exposes the following Prometheus metrics at the `/metrics` endpoint:

- `flagsmith_sse_subscribers_active`: number of active subscribers
- `flagsmith_sse_subscribers_total`: total number of subscribers
- `flagsmith_sse_redis_commands_total`, with labels `command=SCAN|PING|SET`
- `flagsmith_sse_redis_errors_total`, with labels `command=SCAN|PING|SET`

## Benchmarking

The SSE service is constrained by:

- The number of open HTTP connections it can keep open at the same time (memory, sockets)
- The number of subscribers that will receive a message after an update (CPU and network)

An 11-core M3 MacBook Pro with 18 GB of memory can support at least 10.000 concurrent subscribers with simultaneous
publishing at ~1 second latency, constrained by the number of open sockets. This was tested with a
[k6 script](benchmark.js) that opens many subscriptions to one environment on the SSE service while pushing updates to
that environment.

You can monitor the load test while it's running by connecting to the SSE service as another subscriber:

```
$ curl -H "Accept:text/event-stream" -N -i http://localhost:8088/sse/environments/load_test/stream
HTTP/1.1 200 OK
Cache-Control: no-cache
Connection: keep-alive
Content-Type: text/event-stream
Date: Mon, 09 Dec 2024 16:20:00 GMT
Transfer-Encoding: chunked

event: environment_updated
data: {"updated_at": 1735229888.76}
retry: 15000

event: environment_updated
data: {"updated_at": 1735229899.44}
retry: 15000
```

The `queue-change` endpoint can achieve at least 20.000 requests per second on the same hardware.

If you want to benchmark Redis itself, you can use its
[first-party benchmarking tools](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/benchmarks/).
