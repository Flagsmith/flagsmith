// =============================================================================
// Warehouse Connection — Types & Mock Data
// =============================================================================

export type WarehouseType = 'snowflake' | 'bigquery' | 'databricks'

export type ConnectionState =
  | 'empty'
  | 'configuring'
  | 'testing'
  | 'connected'
  | 'error'

export type WarehouseConfig = {
  type: WarehouseType
  accountUrl: string
  database: string
  schema: string
  warehouse: string
  user: string
  authMethod: string
  privateKey: string
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
    description: 'Connected warehouse',
    icon: 'snowflake',
    label: 'Snowflake',
    type: 'snowflake',
  },
  {
    available: false,
    description: 'Coming Soon',
    icon: 'database',
    label: 'BigQuery',
    type: 'bigquery',
  },
  {
    available: false,
    description: 'Coming Soon',
    icon: 'database',
    label: 'Databricks',
    type: 'databricks',
  },
]

export const MOCK_CONFIG: WarehouseConfig = {
  accountUrl: 'https://myorg.snowflakecomputing.com',
  authMethod: 'Key Pair',
  database: 'FLAGSMITH_PROD',
  privateKey:
    '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASC...',
  schema: 'PUBLIC',
  type: 'snowflake',
  user: 'FLAGSMITH_SVC',
  warehouse: 'COMPUTE_WH',
}

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
    "JWT token authentication failed: Invalid private key format. Expected PKCS#8 PEM format but received PKCS#1. Please check your key pair configuration and ensure the private key begins with '-----BEGIN PRIVATE KEY-----'.",
  timestamp: 'Apr 8, 2026 — 14:22 UTC',
}

export const MOCK_CONNECTION_DETAILS: ConnectionDetail[] = [
  { label: 'Database', value: 'FLAGSMITH_PROD' },
  { label: 'Schema', value: 'PUBLIC' },
  { label: 'Warehouse', value: 'COMPUTE_WH' },
  { label: 'User', value: 'FLAGSMITH_SVC' },
  { label: 'Private Key', masked: true, value: '••••••••••••••••  ...a8f2' },
]

export const TESTING_STEPS = [
  'Resolving hostname...',
  'Establishing TLS connection...',
  'Authenticating credentials...',
  'Verifying schema access...',
]
