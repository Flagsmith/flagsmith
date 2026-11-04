---
title: Connect ClickHouse
sidebar_label: ClickHouse
sidebar_position: 1
slug: /experimentation/connect-clickhouse
description: Store and query experiment events in your own ClickHouse instance.
---

import CodeBlock from '@theme/CodeBlock'; import eventsSql from '../../../../experimentation/clickhouse/events.sql?raw';

:::info Beta

Experimentation is in beta.

:::

Instead of the managed Flagsmith warehouse, you can store experiment events in your own **ClickHouse** instance. It must
be reachable from Flagsmith: on Flagsmith Cloud, over the internet; when self-hosting, from your Flagsmith API and
warehouse delivery.

1. Configure your instance by running the following against it, using an administrative user (the statements require
   `CREATE USER`, `GRANT`, `CREATE DATABASE` and `CREATE TABLE` privileges). Replace `<USER>` and `<YOUR_PASSWORD>` with
   your own values. This is a one-off setup step; the same SQL is available to copy from the Flagsmith dashboard.

   <CodeBlock language="sql">{eventsSql}</CodeBlock>

   ```sql
   -- Create a dedicated user for Flagsmith
   CREATE USER IF NOT EXISTS <USER>
       IDENTIFIED WITH sha256_password BY '<YOUR_PASSWORD>';

   -- Allow it to write and read experiment events
   GRANT SELECT, INSERT ON flagsmith_exp.events TO <USER>;

   -- Allow it to check the events table exists
   GRANT SHOW TABLES, SHOW COLUMNS ON flagsmith_exp.* TO <USER>;
   ```

2. Go to **Environment Settings › Warehouse**, select **ClickHouse** and enter your connection details: host, HTTPS port
   (8443 by default), database (`flagsmith_exp` by default), and the username and password of the user you created in
   step 1.
3. Click **Test connection**. Once the test succeeds, save the connection.
4. On Flagsmith Cloud, click **Send your first event** on the connection card to verify events are arriving in your
   warehouse; the button disappears once the first event is received.

Connections use the ClickHouse HTTP(S) interface, with TLS enabled by default.

Experiment results and exposures are computed from your ClickHouse instance.
