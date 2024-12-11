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

At least one SSE service instance and one NATS node are required for real-time updates to work. The SSE service will
reject subscriptions from client applications if NATS is unavailable.

Both NATS and the SSE service can be scaled horizontally to handle more concurrent subscribers and for reliability.

## Message deliverability

Clients that use SSE can only receive data and not send data. As such, they cannot acknowledge they have received an
update from the SSE service. The SSE service will only advance a client's NATS consumer if it was able to send an update
message over TCP. Deliverability will be limited by the reliability of your clients' TCP connections. This is a
constraint of the current real-time implementation of all Flagsmith SDKs, which does not have a way to acknowledge
received messages.

If an environment was updated in the past hour, any client that subscribes to it using the SSE service will immediately
receive the latest update timestamp. This increases reliability in the event of reconnections and undetectable delivery
failures.

The SSE service sends a keep-alive message every 15 seconds if nothing was sent. This is to prevent load balancers, NAT
gateways or other proxies from closing otherwise inactive connections.

## Latency

The goal is to minimise **end-to-end latency**, which is the time taken between the Flagsmith API acknowledging an
environment update, and a client getting notified of this update over SSE. Ignoring network delays, this will mainly
depend on:

- How often the [task processor](https://docs.flagsmith.com/deployment/configuration/task-processor) is polling the API
  for new tasks (by default 2 seconds)
- How long the "environment updated" tasks take to execute (varies on task processor and database load)
- How fast NATS can acknowledge the update (usually milliseconds)
- How fast NATS can notify all relevant SSE instances (usually milliseconds)
- How fast the SSE service can get updates from NATS and notify its subscribers (usually milliseconds, depending on
  load)

## Storage

NATS stores a timestamp of when each environment was last updated. This timestamp is persisted for about an hour to
allow updates to distribute while limiting how much data can be stored. JetStream can be configured to prefer in-memory
storage if persistence is not required, though some state is always persisted by JetStream such as Raft consensus data.

The only persisted data is the stream named `environments-stream`.

<details>

<summary>Inspecting the stream with the NATS CLI</summary>

```
$ nats str info environments-stream
Information for Stream environments-stream created 2024-12-10 16:19:26

              Subjects: flagsmith.environment.>
              Replicas: 1
               Storage: File

Options:

             Retention: Limits
       Acknowledgments: true
        Discard Policy: Old
      Duplicate Window: 2m0s
     Allows Msg Delete: true
          Allows Purge: true
        Allows Rollups: false

Limits:

      Maximum Messages: unlimited
   Maximum Per Subject: 1
         Maximum Bytes: unlimited
           Maximum Age: 1h0m0s
  Maximum Message Size: unlimited
     Maximum Consumers: unlimited

State:

              Messages: 1
                 Bytes: 85 B
        First Sequence: 160,077 @ 2024-12-11 00:47:42
         Last Sequence: 160,077 @ 2024-12-11 00:47:42
      Active Consumers: 4
    Number of Subjects: 1


```

</details>

## Security

Subscribing to real-time updates via the SSE service does not require authentication. The SSE service allows all CORS
requests on all endpoints.

The task processor authenticates with the SSE service when publishing an update by using a shared secret. This secret is
configured using the `SSE_AUTHENTICATION_TOKEN` environment variable. For example:

```
curl -X POST -H "Authorization: Token ..." -H "Content-Type: application/json" -d'{"updated_at":123}' http://localhost:8088/sse/environments/abcxyz/queue-change
```

## Monitoring

Make sure you are [monitoring the task processor](/deployment/configuration/task-processor#monitoring), as the SSE
service depends on it.

The SSE service exposes two health check endpoints, which can be used for liveness and readiness checks:

- `GET /livez` responds with 200 if the SSE service can accept incoming connections.
- `GET /readyz` responds with 200 if the SSE service is available and connected to NATS. This only checks the internal
  NATS connection state and does not generate NATS traffic.

NATS provides its own [tools for monitoring](https://docs.nats.io/running-a-nats-service/nats_admin/monitoring).

## Metrics

TODO: The following is not implemented!

The SSE service exposes the following Prometheus metrics at the `/metricsz` endpoint:

- `flagsmith_sse_subscribers`: number of active subscribers
- `flagsmith_sse_subscribers_total`: total number of subscribers
- `flagsmith_sse_http_errors_total`, with labels `message=keepalive|data|healthcheck`
- `flagsmith_sse_http_writes_total`, with labels `message=keepalive|data|healthcheck`
- `flagsmith_sse_nats_errors_total`, with labels
  `operation=connect|publish|create_jetstream|create_consumer|pull|read|ack`

We provide a Grafana dashboard for these metrics.

NATS also provides a Grafana dashboard and can be configured to
[expose Prometheus metrics](https://github.com/nats-io/prometheus-nats-exporter/blob/main/walkthrough/README.md).

## Benchmarking

The SSE service is constrained by:

- The number of open HTTP connections it can keep open at the same time (memory, sockets)
- The number of subscribers that will receive a message after an update (CPU and network)

An 11-core M3 MacBook Pro with 18 GB of memory can support at least 15.000 concurrent subscribers with simultaneous
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

data: {"updated_at":1}

data: {"updated_at":2}
```

The `queue-change` endpoint can achieve at least 20.000 requests per second on the same hardware.

If you want to benchmark NATS itself, you can use its
[first-party benchmarking tools](https://docs.nats.io/using-nats/nats-tools/nats_cli/natsbench).
