import { DATABRICKS_DEFAULTS } from './databricksConfig'

type DatabricksSetupSqlParams = {
  catalog?: string
  schema?: string
  clientId?: string
}

export const getDatabricksSetupSql = ({
  catalog,
  clientId,
  schema,
}: DatabricksSetupSqlParams = {}): string => {
  const c = catalog?.trim() || '<CATALOG>'
  const s = schema?.trim() || DATABRICKS_DEFAULTS.schema
  const principal = clientId?.trim() || '<CLIENT_ID>'
  return `-- Create the schema and events table
CREATE SCHEMA IF NOT EXISTS ${c}.${s};

CREATE TABLE IF NOT EXISTS ${c}.${s}.events (
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
GRANT USE CATALOG ON CATALOG ${c} TO \`${principal}\`;
GRANT USE SCHEMA ON SCHEMA ${c}.${s} TO \`${principal}\`;
GRANT SELECT, MODIFY ON TABLE ${c}.${s}.events TO \`${principal}\`;`
}

export const DATABRICKS_SETUP_SQL_LABEL =
  'Run once in the Databricks SQL editor to create the events table and grant access'
