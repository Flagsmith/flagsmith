---
title: Connect Databricks
sidebar_label: Connect Databricks
sidebar_position: 2.5
description: Store and query experiment events in your own Databricks workspace.
---

:::info Enterprise beta

Experimentation is in beta on **Enterprise** plans. [Get in touch](https://www.flagsmith.com/contact-us) to join.

:::

:::info Early access

Databricks connections are in early access. [Get in touch](https://www.flagsmith.com/contact-us) to enable them for your
organisation.

:::

Flagsmith writes experiment events to a table in your Databricks workspace and computes experiment results by querying
it there. Each environment has one [warehouse connection](/experimentation/connect-a-warehouse).

## Before you start

- A workspace with Unity Catalog enabled.
- A workspace region where Databricks supports Zerobus Ingest, which Flagsmith uses to write events. See
  [Databricks' region support](https://docs.databricks.com/aws/en/resources/feature-region-support#ingestion).
- A serverless SQL warehouse.
- Workspace admin access, to create a service principal.
- A catalog where you can create schemas.

Databricks Free Edition is not supported.

## 1. Note your connection details

- **Server hostname**: from **SQL Warehouses › your warehouse › Connection details**. You can paste your workspace URL
  instead; Flagsmith keeps only the hostname.
- **Workspace ID**: the number after `?o=` in your workspace URL. Flagsmith fills it in if you paste the full URL as the
  hostname.
- **Region**: shown under the workspace name in the workspace switcher, e.g. `us-east-1`, `eastus2` or `us-central1`.
- **Warehouse ID**: the last part of the **HTTP path** in Connection details. Pasting the full HTTP path is fine.
- **Catalog**: the catalog the events table will live in, e.g. `workspace`.

## 2. Create a service principal

1. Go to **Settings › Identity and access › Service principals**.
2. Click **Add service principal › Add new** and name it `flagsmith`.
3. Open **Secrets**, click **Generate secret**, and add the `sql` scope only.
4. Copy the client ID and secret. The secret is shown only once.

:::important

Without the `sql` scope the connection test fails, and a secret's scopes can't be changed once it is generated. Secrets
expire after the lifetime you choose; see [Rotate the secret](#rotate-the-secret).

:::

## 3. Let it use the SQL warehouse

Go to **SQL Warehouses**, select your warehouse, click **Permissions**, add `flagsmith` and choose **Can use**.

## 4. Create the events table

Run this once in the **SQL editor** as an admin. Replace `<CATALOG>` with your catalog and `<CLIENT_ID>` with the
service principal's client ID. It is safe to run more than once.

```sql
-- Create the schema and events table
CREATE SCHEMA IF NOT EXISTS <CATALOG>.flagsmith_exp;

CREATE TABLE IF NOT EXISTS <CATALOG>.flagsmith_exp.events (
  environment_key STRING NOT NULL,
  event           STRING NOT NULL,
  feature_name    STRING,
  timestamp       TIMESTAMP NOT NULL,
  collected_at    TIMESTAMP,
  identifier      STRING NOT NULL,
  value           STRING,
  traits          STRING,
  metadata        STRING,
  sdk_language    STRING,
  sdk_version     STRING
)
CLUSTER BY (environment_key, event, feature_name, timestamp);

-- Allow the Flagsmith service principal to read and write experiment events
GRANT USE CATALOG ON CATALOG <CATALOG> TO `<CLIENT_ID>`;
GRANT USE SCHEMA ON SCHEMA <CATALOG>.flagsmith_exp TO `<CLIENT_ID>`;
GRANT SELECT, MODIFY ON TABLE <CATALOG>.flagsmith_exp.events TO `<CLIENT_ID>`;
```

If you use a schema other than `flagsmith_exp`, use the same name in the script and in Flagsmith.

Flagsmith doesn't create or alter the table, so keep it a managed table with exactly these columns and types. Default
storage works; you don't need an external location.

## 5. Connect in Flagsmith

1. Go to **Environment Settings › Warehouse** and select **Databricks**.
2. Fill in the details from step 1 and a name under **Name this warehouse**. Leave **Schema** as `flagsmith_exp`.
3. Enter the **Client ID** and **Client secret** from step 2.
4. Click **Test connection**. Once it succeeds, click **Save and continue**.
5. On the connection card, click **Send your first event**. The status changes from **Pending Connection** to
   **Connected** once the event arrives.

<!-- Screenshot: docs/static/img/experimentation/warehouse-databricks-form.png — the Databricks connection form, filled with dummy values -->

If the test fails, you can save anyway and test again later, but events won't be delivered until it succeeds.

The test doesn't check **Region**. A wrong region only shows up as an error on the connection card once events are
delivered.

## Manage the connection

### Rotate the secret

1. Generate a new `sql`-scoped secret for the service principal before the old one expires.
2. Edit the connection and enter the client ID and new secret.
3. Click **Test connection**, then **Save changes**.

Leaving the secret blank keeps the current credentials.

### Change workspace

The server hostname can't be changed. Disconnect and create a new connection.

## Troubleshooting

Errors show as the result of **Test connection**, or on the connection card with status **Errored** when event delivery
fails.

| Message                                                                                          | Where      | What to do                                                                                                                           |
| ------------------------------------------------------------------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Authentication failed.                                                                           | Test, card | Check the client ID and secret, or generate a new secret if it expired. On the card, also check **Workspace ID**.                    |
| The service principal secret must allow the sql scope. Generate a new secret with the sql scope. | Test, card | Generate a new secret with the `sql` scope ([step 2](#2-create-a-service-principal)) and update the connection.                      |
| The workspace ID does not match this workspace.                                                  | Test       | Use the number after `?o=` from the same workspace as the server hostname.                                                           |
| SQL warehouse not found.                                                                         | Test       | Check **Warehouse ID**, and that the service principal has **Can use** on the warehouse ([step 3](#3-let-it-use-the-sql-warehouse)). |
| Database does not exist.                                                                         | Test       | Check **Catalog** and **Schema**, and that you ran the script in [step 4](#4-create-the-events-table).                               |
| Events table not found in the configured database. Run the setup SQL to create it.               | Test, card | Run the setup SQL that Flagsmith shows, which has your catalog, schema and client ID filled in.                                      |
| The Databricks workspace rejected the request.                                                   | Test, card | Check that the service principal has **Can use** on the warehouse, and that you ran the step 4 script with its client ID.            |
| The SQL warehouse is starting. Test the connection again in a few minutes.                       | Test       | Wait for the warehouse to start, then test again.                                                                                    |
| Could not connect to the host.                                                                   | Test, card | Check **Server hostname**. On the card, also check **Region**, and that Zerobus Ingest is available there.                           |
| The events table is missing or the service principal lacks access to it. Run the setup SQL.      | Card       | Run the step 4 script again with the right catalog, schema and client ID.                                                            |
| Permission denied on the events table.                                                           | Card       | Run the `GRANT` statements in step 4 again.                                                                                          |
| The warehouse rejected the events. Check that the events table matches the expected schema.      | Card       | Make the table's columns and types match the step 4 script exactly, as a managed table.                                              |
| Connection failed.                                                                               | Test       | [Contact support](/support/).                                                                                                        |
