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
can store experiment events in two ways: in the [Flagsmith database](#flagsmith-database) or in
[your own warehouse](#your-own-warehouse).

## Turning it on

Set `EXPERIMENTATION_ENABLED=true` on the Flagsmith API. The **Warehouse** tab doesn't appear without it. See
[environment variables](/deployment-self-hosting/core-configuration/environment-variables).

## Flagsmith database

:::warning

For evaluating experimentation only. Events share the database that serves your flags, so they can slow Flagsmith down.
For production, [connect your own warehouse](#your-own-warehouse).

:::

Events are stored in the database Flagsmith already runs on, and the SDKs send them to your Flagsmith API. There is
nothing extra to run. This only works when that database is PostgreSQL.

1. Go to **Environment Settings › Warehouse**.
2. Select **Flagsmith database** and click **Enable**, then confirm.

![The Warehouse tab with the Flagsmith database card selected and the Enable button](/img/experimentation/warehouse-flagsmith-database.png)

The connection shows **Connected** straight away. If Flagsmith can't read the events table, it shows **Errored** with
the reason; fix it and click **Test connection** on the card.

Set each SDK's events URL to the URL shown on the card; see [SDK events URL](#sdk-events-url). To verify events arrive,
click **Send your first event**.

![A connected Flagsmith database card showing the events URL, an SDK snippet and the Send your first event button](/img/experimentation/warehouse-flagsmith-database-connected.png)

The connection has no settings to edit. To stop storing events, delete the connection; events already stored stay in the
table.

## Your own warehouse

Events are delivered to your own [ClickHouse](/experimentation/connect-a-warehouse#bring-your-own-clickhouse),
[Databricks](/experimentation/connect-databricks) or [PostgreSQL](/experimentation/connect-postgresql).

- Also run the event ingestion service, Kafka and warehouse delivery. See [Deploying](#deploying).
- Suits higher event volumes. See
  [Sizing experimentation](/deployment-self-hosting/scaling-and-performance/sizing-and-scaling#sizing-experimentation).

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
