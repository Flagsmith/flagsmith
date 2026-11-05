---
title: Connect a Warehouse
sidebar_label: Connect a Warehouse
sidebar_position: 2
description: Choose where experiment events are stored, from the managed Flagsmith warehouse to your own database.
---

:::info Beta

Experimentation is in beta.

:::

Experiment data (exposures and conversion events) is stored and queried in a data warehouse. Each environment has one
warehouse connection, and it must be in place before you can create experiments.

:::note Self-hosted

The managed Flagsmith warehouse is only available on Flagsmith Cloud. When self-hosting, see
[Self-Hosting and Open Source](/experimentation/self-hosting).

:::

:::note Plans

On Flagsmith Cloud, connecting your own ClickHouse, Databricks or PostgreSQL requires a
[Scale-Up or Enterprise subscription](https://www.flagsmith.com/pricing). Self-hosted Flagsmith has no plan restriction.

:::

## Connect the Flagsmith warehouse

The **Flagsmith** warehouse is managed and hosted by Flagsmith. There is nothing to provision or configure.

1. Go to **Environment Settings › Warehouse**.
2. Select **Flagsmith** and click **Enable**, then confirm.

![The Warehouse tab with the Flagsmith managed warehouse selected](/img/experimentation/warehouse-tab.png)

The connection is created immediately. To verify that events can flow, click **Send your first event** and Flagsmith
sends a test event on your behalf. The connection shows **Pending Connection** while it waits for the first event, and
switches to **Connected** as soon as the environment's first event arrives; an event sent from your own application
counts too, not just the test event.

:::note

Processing the first event can take up to a few hours. The status refreshes about once a minute while you keep the
Warehouse tab open.

:::

Once connected, the warehouse card shows the total number of events received and the number of unique event names, which
is useful to verify that instrumentation data is arriving.

## Connection statuses

The current status is shown on the warehouse card in **Environment Settings › Warehouse**.

- **Created**: the connection exists but no events have been received yet.
- **Pending Connection**: waiting for the first event to arrive.
- **Connected**: events have been received; you are ready to run experiments.
- **Errored**: the card shows the reason. See Troubleshooting for
  [Databricks](/experimentation/connect-databricks#troubleshooting) or
  [PostgreSQL](/experimentation/connect-postgresql#troubleshooting); otherwise [contact support](/support/).

## Bring your own warehouse

To store experiment events in your own warehouse, and have Flagsmith compute results there, connect one of:

- [ClickHouse](/experimentation/connect-clickhouse)
- [Databricks](/experimentation/connect-databricks)
- [PostgreSQL](/experimentation/connect-postgresql), or a PostgreSQL-compatible service. It suits low to moderate event
  volumes.

## Coming soon

Bring your own warehouse: connections for **Snowflake** and **BigQuery**.
