// =============================================================================
// Warehouse Connection — Types & Mock Data
// =============================================================================

export type WarehouseType = 'snowflake' | 'bigquery' | 'databricks'

export type ConnectionState =
  | 'empty'
  | 'configuring'
  | 'pending_customer_setup'
  | 'testing'
  | 'connected'
  | 'error'

/**
 * Config fields the customer fills in. Mirrors issue #7276 — no credential
 * fields; the server generates the RSA keypair and returns a public key + a
 * setup script the customer runs in Snowflake themselves.
 */
export type WarehouseConfig = {
  type: WarehouseType
  accountIdentifier: string
  warehouse: string
  database: string
  schema: string
  role: string
  user: string
}

export type ConnectionStats = {
  lastDelivery: string
  lastDeliveryDate: string
  flagEvaluations24h: number
  flagEvaluationsTrend: string
  customEvents24h: number
  customEventsTrend: string
}

export type ConnectionError = {
  message: string
  timestamp: string
  lastSuccessful: string
  lastSuccessfulDate: string
}

export type ConnectionDetail = {
  label: string
  value: string
  masked?: boolean
}

export type WarehouseTypeOption = {
  type: WarehouseType
  icon: string
  label: string
  description: string
  available: boolean
}

// =============================================================================
// Mock Data
// =============================================================================

export const WAREHOUSE_TYPES: WarehouseTypeOption[] = [
  {
    available: true,
    description: 'Cloud data warehouse',
    icon: 'snowflake',
    label: 'Snowflake',
    type: 'snowflake',
  },
  {
    available: false,
    description: 'Google Cloud data warehouse',
    icon: 'database',
    label: 'BigQuery',
    type: 'bigquery',
  },
  {
    available: false,
    description: 'Unified analytics platform',
    icon: 'database',
    label: 'Databricks',
    type: 'databricks',
  },
]

export const MOCK_CONFIG: WarehouseConfig = {
  accountIdentifier: 'xy12345.us-east-1',
  database: 'FLAGSMITH',
  role: 'FLAGSMITH_LOADER',
  schema: 'ANALYTICS',
  type: 'snowflake',
  user: 'FLAGSMITH_SERVICE',
  warehouse: 'COMPUTE_WH',
}

export const MOCK_PUBLIC_KEY =
  'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwK3k7mB9G8o7fQ6X4lTz' +
  'VpS2gI2vL5TXyBqcJ9xN3fWZpLeEgDvKwYc6M7HRqL8nT2Jf4sYh1DaPBqXFbWzC' +
  'oLvP8rKmRpgFq7GPdVwH5cX2bYyNhYeZ7CvIoR9N3mvXLmMBGkKQQkGVKLmN6pQL' +
  'fWxG2kPqBhHvWLVuF4mBzNjMqLBn2Xb5Y7KJj8DwLcLK6sGnNWk6xKwqNtnDr6vP' +
  'RPAJm6xKZLMdV4X9rYbQGBnNvJw4mXtLmPqF8QXNQ1VpYZmPEqC8uBxNKfLpVcLw' +
  'N4kZQIDAQAB'

export const MOCK_SETUP_SCRIPT = `-- Flagsmith Analytics — Snowflake setup
-- Run as a user with SYSADMIN role.

USE ROLE SYSADMIN;

-- Dedicated role for Flagsmith ingest
CREATE ROLE IF NOT EXISTS FLAGSMITH_LOADER;

-- Service user, no password (key-pair auth only)
CREATE USER IF NOT EXISTS FLAGSMITH_SERVICE
  DEFAULT_ROLE = FLAGSMITH_LOADER
  DEFAULT_WAREHOUSE = COMPUTE_WH
  DEFAULT_NAMESPACE = FLAGSMITH.ANALYTICS;

-- Register Flagsmith's public key for authentication
ALTER USER FLAGSMITH_SERVICE SET RSA_PUBLIC_KEY = '${MOCK_PUBLIC_KEY}';

-- Database + schema for analytics ingest
CREATE DATABASE IF NOT EXISTS FLAGSMITH;
CREATE SCHEMA IF NOT EXISTS FLAGSMITH.ANALYTICS;

-- Grants
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE FLAGSMITH_LOADER;
GRANT USAGE ON DATABASE FLAGSMITH TO ROLE FLAGSMITH_LOADER;
GRANT USAGE ON SCHEMA FLAGSMITH.ANALYTICS TO ROLE FLAGSMITH_LOADER;
GRANT CREATE TABLE ON SCHEMA FLAGSMITH.ANALYTICS TO ROLE FLAGSMITH_LOADER;
GRANT SELECT, INSERT, UPDATE, DELETE
  ON FUTURE TABLES IN SCHEMA FLAGSMITH.ANALYTICS
  TO ROLE FLAGSMITH_LOADER;

GRANT ROLE FLAGSMITH_LOADER TO USER FLAGSMITH_SERVICE;`

export const MOCK_STATS: ConnectionStats = {
  customEvents24h: 84210,
  customEventsTrend: '+5% vs yesterday',
  flagEvaluations24h: 1284039,
  flagEvaluationsTrend: '+12% vs yesterday',
  lastDelivery: '2 minutes ago',
  lastDeliveryDate: 'Apr 8, 2026 — 14:37 UTC',
}

export const MOCK_ERROR: ConnectionError = {
  lastSuccessful: '3 hours ago',
  lastSuccessfulDate: 'Apr 8, 2026 — 11:15 UTC',
  message:
    "JWT token authentication failed. Snowflake couldn't verify the public key registered on the FLAGSMITH_SERVICE user. Re-run the setup script to re-register the key, or check that the user exists.",
  timestamp: 'Apr 8, 2026 — 14:22 UTC',
}

export const MOCK_CONNECTION_DETAILS: ConnectionDetail[] = [
  { label: 'Account Identifier', value: 'xy12345.us-east-1' },
  { label: 'Database', value: 'FLAGSMITH' },
  { label: 'Schema', value: 'ANALYTICS' },
  { label: 'Warehouse', value: 'COMPUTE_WH' },
  { label: 'Role', value: 'FLAGSMITH_LOADER' },
  { label: 'User', value: 'FLAGSMITH_SERVICE' },
]

export const TESTING_STEPS = [
  'Resolving hostname...',
  'Establishing TLS connection...',
  'Authenticating with key pair...',
  'Verifying schema access...',
]
