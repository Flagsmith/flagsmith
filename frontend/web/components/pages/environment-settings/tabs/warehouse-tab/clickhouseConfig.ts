import { ClickHouseConfig } from 'common/types/responses'

export const CLICKHOUSE_DEFAULTS: ClickHouseConfig = {
  database: 'flagsmith',
  host: '',
  port: 9440,
  secure: true,
  username: 'default',
}

export type ClickHouseFormState = {
  name: string
  host: string
  port: string
  database: string
  username: string
  password: string
  secure: boolean
}

export type ClickHouseFormData = {
  name: string
  config: ClickHouseConfig
  credentials?: { password: string }
}

export const isValidPort = (port: string): boolean => {
  const trimmed = port.trim()
  const value = Number(trimmed)
  return (
    /^\d+$/.test(trimmed) &&
    Number.isInteger(value) &&
    value >= 1 &&
    value <= 65535
  )
}

export const isClickHouseFormValid = (
  form: ClickHouseFormState,
  isEdit: boolean,
): boolean =>
  !!form.name.trim() &&
  !!form.host.trim() &&
  isValidPort(form.port) &&
  !!form.database.trim() &&
  !!form.username.trim() &&
  (isEdit || !!form.password)

export const buildClickHousePayload = (
  form: ClickHouseFormState,
): ClickHouseFormData => ({
  config: {
    database: form.database.trim(),
    host: form.host.trim(),
    port: Number(form.port.trim()),
    secure: form.secure,
    username: form.username.trim(),
  },
  credentials: form.password ? { password: form.password } : undefined,
  name: form.name.trim(),
})

export const canTestClickHouseConnection = (
  form: ClickHouseFormState,
): boolean =>
  !!form.host.trim() &&
  isValidPort(form.port) &&
  !!form.database.trim() &&
  !!form.username.trim() &&
  !!form.password

export const isClickHouseConfigDirty = (
  form: ClickHouseFormState,
  initialConfig: ClickHouseConfig | undefined,
): boolean => {
  const initial = { ...CLICKHOUSE_DEFAULTS, ...initialConfig }
  return (
    form.host.trim() !== initial.host ||
    Number(form.port.trim()) !== initial.port ||
    form.database.trim() !== initial.database ||
    form.username.trim() !== initial.username ||
    form.secure !== initial.secure ||
    !!form.password
  )
}
