import { SNOWFLAKE_DEFAULTS } from './snowflakeConfig'

type SnowflakeSetupSqlParams = {
  warehouse?: string
  database?: string
  schema?: string
  role?: string
  user?: string
}

// The events table mirrors experimentation/snowflake/events.sql; a parity test keeps them aligned.
export const getSnowflakeSetupSql = (
  params: SnowflakeSetupSqlParams = {},
): string => {
  const warehouse = params.warehouse?.trim() || SNOWFLAKE_DEFAULTS.warehouse
  const database = params.database?.trim() || SNOWFLAKE_DEFAULTS.database
  const schema = params.schema?.trim() || SNOWFLAKE_DEFAULTS.schema
  const role = params.role?.trim() || SNOWFLAKE_DEFAULTS.role
  const user = params.user?.trim() || SNOWFLAKE_DEFAULTS.user
  return `-- Create the role, warehouse, database, schema and events table
USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS ${role};

CREATE WAREHOUSE IF NOT EXISTS ${warehouse}
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

CREATE DATABASE IF NOT EXISTS ${database};
CREATE SCHEMA IF NOT EXISTS ${database}.${schema};

CREATE TABLE IF NOT EXISTS ${database}.${schema}.EVENTS (
  ENVIRONMENT_KEY STRING NOT NULL,
  EVENT           STRING NOT NULL,
  FEATURE_NAME    STRING,
  TIMESTAMP       TIMESTAMP_NTZ NOT NULL,
  COLLECTED_AT    TIMESTAMP_NTZ,
  IDENTIFIER      STRING NOT NULL,
  VALUE           STRING,
  TRAITS          STRING,
  METADATA        STRING,
  SDK_LANGUAGE    STRING,
  SDK_VERSION     STRING
);

-- Allow the Flagsmith role to read and write experiment events
GRANT USAGE ON WAREHOUSE ${warehouse} TO ROLE ${role};
GRANT USAGE ON DATABASE ${database} TO ROLE ${role};
GRANT USAGE ON SCHEMA ${database}.${schema} TO ROLE ${role};
GRANT SELECT, INSERT ON TABLE ${database}.${schema}.EVENTS TO ROLE ${role};

-- Create the Flagsmith service user with your public key
CREATE USER IF NOT EXISTS ${user}
  TYPE = SERVICE
  DEFAULT_ROLE = ${role}
  DEFAULT_WAREHOUSE = ${warehouse}
  RSA_PUBLIC_KEY = '<PUBLIC_KEY>';
GRANT ROLE ${role} TO USER ${user};`
}

export const SNOWFLAKE_KEY_PAIR_COMMANDS = `openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out flagsmith_key.p8 -nocrypt
openssl rsa -in flagsmith_key.p8 -pubout -out flagsmith_key.pub`

export const SNOWFLAKE_SETUP_SQL_LABEL =
  'Run once in a Snowflake SQL worksheet to create the events table and grant access'
