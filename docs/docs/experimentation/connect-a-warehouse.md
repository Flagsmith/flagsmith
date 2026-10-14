---
title: Connect a Warehouse
sidebar_label: Connect a Warehouse
sidebar_position: 2
description: Enable the managed Flagsmith warehouse to store and query experiment events.
---

import CodeBlock from '@theme/CodeBlock'; import eventsSql from '../../../experimentation/clickhouse/events.sql?raw';

:::info Enterprise beta

Experimentation is in beta on **Enterprise** plans. [Get in touch](https://www.flagsmith.com/contact-us) to join.

:::

Experiment data (exposures and conversion events) is stored and queried in a data warehouse. Each environment has one
warehouse connection, and it must be in place before you can create experiments.

## Connect the Flagsmith warehouse

The **Flagsmith** warehouse is managed and hosted by Flagsmith. There is nothing to provision or configure, and there is
no additional cost — it is included in your Enterprise plan.

1. Go to **Environment Settings > Warehouse**.
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

<!-- Screenshot: connected warehouse card with event stats -->

### Connection statuses

The current status is shown on the warehouse card in **Environment Settings > Warehouse**.

- **Created**: the connection exists but no events have been received yet.
- **Pending Connection**: waiting for the first event to arrive.
- **Connected**: events have been received; you are ready to run experiments.
- **Errored**: something went wrong; [contact support](/support/).

## Bring your own ClickHouse

Instead of the managed Flagsmith warehouse, you can store experiment events in your own **ClickHouse** instance.

1. Configure your instance by running the following against it, using an administrative user (the statements require
   `CREATE USER`, `GRANT`, `CREATE DATABASE` and `CREATE TABLE` privileges). Replace `<USER>` and `<CHANGE_ME_PASSWORD>`
   with your own values. This is a one-off setup step; the same SQL is available to copy from the Flagsmith dashboard.

   <CodeBlock language="sql">{eventsSql}</CodeBlock>

   ```sql
   -- Create a dedicated user for Flagsmith
   CREATE USER IF NOT EXISTS <USER>
       IDENTIFIED WITH sha256_password BY '<CHANGE_ME_PASSWORD>';

   -- Allow it to write and read experiment events
   GRANT SELECT, INSERT ON flagsmith_exp.events TO <USER>;

   -- Allow it to check the events table exists
   GRANT SHOW TABLES, SHOW COLUMNS ON flagsmith_exp.* TO <USER>;
   ```

2. Go to **Environment Settings > Warehouse**, select **ClickHouse** and enter your connection details: host, HTTPS port
   (8443 by default), database (`flagsmith_exp` by default), and the username and password of the user you created in
   step 1.
3. Click **Test connection**. Once the test succeeds, save the connection.
4. Click **Send your first event** on the connection card to verify events are arriving in your warehouse; the button
   disappears once the first event is received.

Connections use the ClickHouse HTTP(S) interface, with TLS enabled by default.

Experiment results and exposure queries are currently computed from the managed Flagsmith warehouse; serving results
directly from your own ClickHouse instance is not supported yet.

## Coming soon

Bring your own warehouse: connections for **Snowflake**, **BigQuery** and **Databricks**, so experiment results are
computed directly in your own data platform.
