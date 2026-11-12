import { PostgresConfig, PostgresSslMode } from 'common/types/responses'
import { isValidPort } from './clickhouseConfig'

export const POSTGRES_DEFAULTS: PostgresConfig = {
  database: '',
  host: '',
  port: 5432,
  schema: 'flagsmith_exp',
  sslmode: 'require',
  username: '',
}

// Unquoted identifiers fold to lowercase, so only lowercase ones match the setup SQL.
const LOWERCASE_IDENTIFIER = /^[a-z_][a-z0-9_]{0,62}$/

export type PostgresFormState = {
  name: string
  host: string
  port: string
  database: string
  schema: string
  username: string
  password: string
  sslmode: PostgresSslMode
}

export type PostgresFormData = {
  name: string
  config: PostgresConfig
  credentials?: { password: string }
}

// Rejects URLs, paths and host:port; a single colon can't be an IPv6 literal.
export const isValidPostgresHost = (host: string): boolean => {
  const value = host.trim()
  return !!value && !/[\s/@]/.test(value) && value.split(':').length !== 2
}

export const isValidPostgresSchema = (schema: string): boolean =>
  LOWERCASE_IDENTIFIER.test(schema.trim())

// The host is locked on edit, so a stored host must not block saving.
const isPostgresConfigValid = (
  form: PostgresFormState,
  isEdit: boolean,
): boolean =>
  (isEdit || isValidPostgresHost(form.host)) &&
  isValidPort(form.port) &&
  !!form.database.trim() &&
  isValidPostgresSchema(form.schema) &&
  !!form.username.trim()

export const isPostgresFormValid = (
  form: PostgresFormState,
  isEdit: boolean,
): boolean =>
  !!form.name.trim() &&
  isPostgresConfigValid(form, isEdit) &&
  (isEdit || !!form.password)

export const canTestPostgresConnection = (
  form: PostgresFormState,
  isEdit: boolean,
): boolean => isPostgresConfigValid(form, isEdit) && !!form.password

const buildPostgresConfig = (form: PostgresFormState): PostgresConfig => ({
  database: form.database.trim(),
  host: form.host.trim(),
  port: Number(form.port.trim()),
  schema: form.schema.trim(),
  sslmode: form.sslmode,
  username: form.username.trim(),
})

export const buildPostgresPayload = (
  form: PostgresFormState,
): PostgresFormData => ({
  config: buildPostgresConfig(form),
  credentials: form.password ? { password: form.password } : undefined,
  name: form.name.trim(),
})

export const isPostgresConfigDirty = (
  form: PostgresFormState,
  initialConfig: PostgresConfig | undefined,
): boolean => {
  const initial = { ...POSTGRES_DEFAULTS, ...initialConfig }
  const config = buildPostgresConfig(form)
  return (
    (Object.keys(POSTGRES_DEFAULTS) as (keyof PostgresConfig)[]).some(
      (key) => config[key] !== initial[key],
    ) || !!form.password
  )
}
