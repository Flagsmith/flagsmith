---
title: Self-Hosting and Open Source
sidebar_label: Self-Hosting and Open Source
sidebar_position: 2.3
description: Choose how self-hosted Flagsmith stores experiment events, and what to deploy for each option.
---

:::info Beta

Experimentation is in beta.

:::

Experimentation works in both the Open Source version and the
[Enterprise Edition](/deployment-self-hosting/enterprise-edition), with no edition restriction. Self-hosted Flagsmith
can store experiment events in two ways.

## Flagsmith database

Events are stored in the PostgreSQL database Flagsmith already runs on, and the SDKs send them to your Flagsmith API.

- Needs only the Flagsmith API; there is nothing extra to run.
- Only works when your Flagsmith database is PostgreSQL.
- Events share your application database, so they add to its size, backups and load.

To set it up, see
[Self-hosted: use the Flagsmith database](/experimentation/connect-a-warehouse#self-hosted-use-the-flagsmith-database).

## Your own warehouse

Events are delivered to your own [ClickHouse](/experimentation/connect-a-warehouse#bring-your-own-clickhouse),
[Databricks](/experimentation/connect-databricks) or [PostgreSQL](/experimentation/connect-postgresql).

- Also run the event ingestion service, Kafka and warehouse delivery. See [Deploying](#deploying).
- Suits higher event volumes. See
  [Sizing experimentation](/deployment-self-hosting/scaling-and-performance/sizing-and-scaling#sizing-experimentation).

## Turning it on

Set `EXPERIMENTATION_ENABLED=true` on the Flagsmith API. The **Warehouse** tab doesn't appear without it. See
[environment variables](/deployment-self-hosting/core-configuration/environment-variables).

## SDK events URL

By default, the SDKs send events to Flagsmith Cloud. Set each SDK's events URL to:

- **Flagsmith database**: your Flagsmith API URL ending in `/api/`, for example `https://flagsmith.example.com/api/`.
- **Your own warehouse**: your event ingestion service's public URL, for example
  `https://events.flagsmith.example.com/`.

The SDKs append `v1/events` themselves. See [Initialise](/experimentation/run-an-experiment#initialise) for each SDK.

## Things to know

- Events with a timestamp more than 10 days in the past or 24 hours in the future are rejected.
- A batch over 2 MiB is rejected whole.
- Flagsmith never deletes events. Monitor the size of your database or warehouse.

## Deploying

- [Docker](/deployment-self-hosting/hosting-guides/docker#experimentation): the
  [`docker-compose.yml`](https://github.com/Flagsmith/flagsmith/blob/main/docker-compose.yml) runs every experimentation
  service, with a local ClickHouse.
- [Kubernetes and OpenShift](/deployment-self-hosting/hosting-guides/kubernetes-openshift#experimentation): the
  [Helm chart](https://github.com/Flagsmith/flagsmith-charts) runs the ingestion service and warehouse delivery, with
  your own Kafka and warehouse.

The source for the [event ingestion service](https://github.com/Flagsmith/ingestion-server) and
[warehouse delivery](https://github.com/Flagsmith/warehouse-delivery) is on GitHub.
