---
title: Deployment guide
sidebar_label: Deployment
sidebar_position: 30
---

## NATS with JetStream

First, deploy NATS with JetStream enabled. NATS nodes can be deployed in
[many different ways](https://docs.nats.io/nats-concepts/overview). If you don't require high availability for real-time
flags, a single NATS can support tens of thousands of clients.

The only required configuration is to enable [JetStream](https://docs.nats.io/nats-concepts/jetstream). In the
[NATS Helm chart](https://github.com/nats-io/k8s/tree/main/helm/charts/nats), set `config.jetstream` to `true`.

If you are using the [NATS CLI](https://github.com/nats-io/natscli) to launch NATS, use the `-js` or `--jetstream` flag:

```
nats-server --jetstream
```

See the [JetStream docs](https://docs.nats.io/running-a-nats-service/configuration/resource_management) for more
details.

### Authentication

By default, NATS allows reading or writing to any subject without authentication. Several
[authentication methods](https://docs.nats.io/running-a-nats-service/configuration/securing_nats/auth_intro) can be
enabled if required.

The SSE service can only authenticate to NATS using URL-based methods.
[Token authentication](https://docs.nats.io/running-a-nats-service/configuration/securing_nats/auth_intro/tokens) is the
simplest method if you don't have other requirements.

## SSE service

Run the `flagsmith/sse:v4.0.0-beta` image, setting thse environment variables:

| Variable name              | Description                                                      | Default                 |
| -------------------------- | ---------------------------------------------------------------- | ----------------------- |
| `NATS_URL`                 | URL of any NATS node                                             | `nats://127.0.0.1:4222` |
| `LISTEN_ADDR`              | Addresses to listen for HTTP connections on                      | `:8088`                 |
| `SSE_AUTHENTICATION_TOKEN` | Shared secret for authentication on the `/queue-change` endpoint | **Required**            |

## API and task processor

The Flagsmith API and task processor need to know about the SSE service. On both the API and task processor, set these
environment variables:

- `SSE_SERVER_BASE_URL` points to the SSE service load balancer. For example: http://my-sse-service:8088
- `SSE_AUTHENTICATION_TOKEN` can be set to any non-empty string, as long as the SSE service and task processor share the
  same value.

## Flagsmith configuration

Make sure the Flagsmith projects you are updating have real-time updates enabled. If not, no tasks will be queued when
its environments are updated.

Lastly, client applications should set their Flagsmith SDK's realtime endpoint URL to the load balancer for the SSE
service.
