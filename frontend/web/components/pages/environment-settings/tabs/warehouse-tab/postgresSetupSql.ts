import { POSTGRES_DEFAULTS } from './postgresConfig'

// Mirrors experimentation/postgres/events.sql; a parity test keeps them aligned.
export const getPostgresSetupSql = (
  schema: string,
): string => `CREATE SCHEMA IF NOT EXISTS ${schema};
CREATE TABLE IF NOT EXISTS ${schema}.events (
  environment_key TEXT NOT NULL,
  event           TEXT NOT NULL,
  feature_name    TEXT,
  timestamp       TIMESTAMPTZ NOT NULL,
  collected_at    TIMESTAMPTZ,
  identifier      TEXT NOT NULL,
  value           TEXT,
  traits          TEXT,
  metadata        TEXT,
  sdk_language    TEXT,
  sdk_version     TEXT
);
CREATE INDEX IF NOT EXISTS events_env_event_feature_ts ON ${schema}.events (environment_key, event, feature_name, timestamp);
CREATE INDEX IF NOT EXISTS events_env_event_identifier_ts ON ${schema}.events (environment_key, event, identifier, timestamp);`

export const getPostgresOnboardingSql = (): string => {
  const schema = POSTGRES_DEFAULTS.schema
  return `-- Create the schema and events table
${getPostgresSetupSql(schema)}

-- Create a dedicated user for Flagsmith
CREATE USER <USER> PASSWORD '<CHANGE_ME_PASSWORD>';

-- Allow it to read and write experiment events
GRANT USAGE ON SCHEMA ${schema} TO <USER>;
GRANT SELECT, INSERT ON ${schema}.events TO <USER>;`
}

export const POSTGRES_SETUP_SQL_LABEL =
  'Run once against your PostgreSQL database to create the events table'
