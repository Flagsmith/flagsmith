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

Flagsmith writes experiment events to a table in your ClickHouse instance and computes experiment results by querying it
there. Each environment has one [warehouse connection](/experimentation/connect-a-warehouse).

## Before you start

- On Flagsmith Cloud, a [Scale-Up or Enterprise subscription](https://www.flagsmith.com/pricing).
- An instance reachable from Flagsmith: on Flagsmith Cloud, over the internet; when self-hosting, from your Flagsmith
  API and warehouse delivery.
- An administrative user with `CREATE USER`, `GRANT`, `CREATE DATABASE` and `CREATE TABLE` privileges, to run the setup
  SQL.
- When self-hosting, the event ingestion service, Kafka and warehouse delivery. See
  [Self-Hosting and Open Source](/experimentation/self-hosting).

## 1. Create the events table and user

Run this once against your instance. Replace `<USER>` and `<YOUR_PASSWORD>` with your own values. The same SQL is
available to copy from the Flagsmith dashboard.

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

If you use a database other than `flagsmith_exp`, use the same name in the script and in Flagsmith.

Flagsmith doesn't create or alter the table, so keep exactly these columns and types.

## 2. Connect in Flagsmith

1. Go to **Environment Settings › Warehouse** and select **ClickHouse**.
2. Fill in the connection details:
   - **Host**: the hostname of your ClickHouse instance, without protocol or port.
   - **Name this warehouse**: any name, e.g. `Production ClickHouse`.
   - **HTTPS port**: the port of the ClickHouse HTTP(S) interface, `8443` by default.
   - **Database Name**: `flagsmith_exp`, unless you changed it.
   - **Username** and **Password**: the user you created in step 1.
   - **Secure connection (TLS)**: always on; it can't be turned off.
3. Click **Test connection**. Once it succeeds, click **Save and continue**. The test checks that Flagsmith can connect
   and that the events table exists. If the test can't connect, you can save anyway and test again later, but events
   won't be delivered until it succeeds. If Flagsmith rejects a field, such as the host, fix it before saving.
4. On Flagsmith Cloud, to verify events reach your table, click **Send your first event** on the connection card; the
   button disappears once the first event arrives.

![The ClickHouse connection form with host, name, HTTPS port, database, username, password and TLS fields](/img/experimentation/warehouse-clickhouse-form.png)

## Manage the connection

### Change the password

Edit the connection, enter the new password, click **Test connection**, then click **Save changes**. Leaving the
password blank keeps the current one.

### Change server

The host can't be changed. To use a different ClickHouse instance, disconnect and create a new connection.

## Troubleshooting

Errors show under a form field, below **Test connection**, or on the connection card with status **Errored** when event
delivery fails.

| Message                                                                            | Where      | What to do                                                                                                |
| ---------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------- |
| Port must be a number between 1 and 65535.                                         | Form       | Fix **HTTPS port**.                                                                                       |
| Host must not target internal or private network addresses.                        | Test, card | On Flagsmith Cloud, use a host with a public address.                                                     |
| Authentication failed.                                                             | Test, card | Check **Username** and **Password**.                                                                      |
| Database does not exist.                                                           | Test, card | Check **Database Name**, and that it matches the database in the setup SQL.                               |
| Events table not found in the configured database. Run the setup SQL to create it. | Test, card | Run the script in [step 1](#1-create-the-events-table-and-user) with the same database as the connection. |
| Could not connect to the host.                                                     | Test, card | Check **Host** and **HTTPS port**, and that the instance accepts HTTPS connections from Flagsmith.        |
| The ClickHouse server rejected the request.                                        | Test, card | Check the instance's logs for the rejected query, and that the user has the grants in step 1.             |
| Connection failed.                                                                 | Test, card | [Contact support](/support/).                                                                             |
