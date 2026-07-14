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
  const value = Number(port)
  return (
    /^\d+$/.test(port) &&
    Number.isInteger(value) &&
    value >= 1 &&
    value <= 65535
  )
}

export const isClickHouseFormValid = (
  form: ClickHouseFormState,
  isEdit: boolean,
): boolean =>
  !!form.name &&
  !!form.host &&
  isValidPort(form.port) &&
  !!form.database &&
  !!form.username &&
  (isEdit || !!form.password)

export const buildClickHousePayload = (
  form: ClickHouseFormState,
): ClickHouseFormData => ({
  config: {
    database: form.database,
    host: form.host,
    port: Number(form.port),
    secure: form.secure,
    username: form.username,
  },
  credentials: form.password ? { password: form.password } : undefined,
  name: form.name,
})
