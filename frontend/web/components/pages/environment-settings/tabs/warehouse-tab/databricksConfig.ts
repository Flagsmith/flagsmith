import { DatabricksConfig } from 'common/types/responses'

export const DATABRICKS_DEFAULTS: DatabricksConfig = {
  catalog: '',
  host: '',
  region: '',
  schema: 'flagsmith_exp',
  warehouse_id: '',
  workspace_id: '',
}

const HOST_SUFFIXES = [
  '.cloud.databricks.com',
  '.azuredatabricks.net',
  '.gcp.databricks.com',
]
const HOSTNAME =
  /^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$/
const WAREHOUSE_ID = /^[A-Za-z0-9]+$/
const IDENTIFIER = /^[A-Za-z0-9_]+$/
const WORKSPACE_ID = /^\d+$/
const REGION = /^[a-z0-9-]+$/
const WORKSPACE_ID_PARAM = /[?&]o=(\d+)/

export type DatabricksFormState = {
  name: string
  host: string
  workspace_id: string
  region: string
  warehouse_id: string
  catalog: string
  schema: string
  client_id: string
  client_secret: string
}

export type DatabricksCredentials = {
  client_id: string
  client_secret: string
}

export type DatabricksFormData = {
  name: string
  config: DatabricksConfig
  credentials?: DatabricksCredentials
}

export const normaliseDatabricksHost = (host: string): string =>
  host
    .trim()
    .replace(/^[a-z][a-z0-9+.-]*:\/\//i, '')
    .split(/[/?#]/)[0]
    .replace(/:\d*$/, '')
    .toLowerCase()

export const normaliseWarehouseId = (warehouseId: string): string => {
  const segments = warehouseId.trim().split('/').filter(Boolean)
  return segments[segments.length - 1] ?? ''
}

export const normaliseRegion = (region: string): string =>
  region.trim().toLowerCase()

export const getWorkspaceIdFromUrl = (url: string): string | null =>
  url.match(WORKSPACE_ID_PARAM)?.[1] ?? null

export const isValidDatabricksHost = (host: string): boolean => {
  const normalised = normaliseDatabricksHost(host)
  return (
    HOSTNAME.test(normalised) &&
    HOST_SUFFIXES.some((suffix) => normalised.endsWith(suffix))
  )
}

export const isValidWarehouseId = (warehouseId: string): boolean =>
  WAREHOUSE_ID.test(normaliseWarehouseId(warehouseId))

export const isValidWorkspaceId = (workspaceId: string): boolean =>
  WORKSPACE_ID.test(workspaceId.trim())

export const isValidRegion = (region: string): boolean =>
  REGION.test(normaliseRegion(region))

export const isValidIdentifier = (value: string): boolean =>
  IDENTIFIER.test(value.trim())

export const hasDatabricksCredentials = (form: DatabricksFormState): boolean =>
  !!form.client_id.trim() && !!form.client_secret

const hasNoCredentials = (form: DatabricksFormState): boolean =>
  !form.client_id.trim() && !form.client_secret

const isDatabricksConfigValid = (form: DatabricksFormState): boolean =>
  isValidDatabricksHost(form.host) &&
  isValidWorkspaceId(form.workspace_id) &&
  isValidRegion(form.region) &&
  isValidWarehouseId(form.warehouse_id) &&
  isValidIdentifier(form.catalog) &&
  isValidIdentifier(form.schema)

export const isDatabricksFormValid = (
  form: DatabricksFormState,
  isEdit: boolean,
): boolean =>
  !!form.name.trim() &&
  isDatabricksConfigValid(form) &&
  (hasDatabricksCredentials(form) || (isEdit && hasNoCredentials(form)))

export const canTestDatabricksConnection = (
  form: DatabricksFormState,
): boolean => isDatabricksConfigValid(form) && hasDatabricksCredentials(form)

const buildDatabricksConfig = (
  form: DatabricksFormState,
): DatabricksConfig => ({
  catalog: form.catalog.trim(),
  host: normaliseDatabricksHost(form.host),
  region: normaliseRegion(form.region),
  schema: form.schema.trim(),
  warehouse_id: normaliseWarehouseId(form.warehouse_id),
  workspace_id: form.workspace_id.trim(),
})

export const buildDatabricksPayload = (
  form: DatabricksFormState,
): DatabricksFormData => ({
  config: buildDatabricksConfig(form),
  credentials: hasDatabricksCredentials(form)
    ? { client_id: form.client_id.trim(), client_secret: form.client_secret }
    : undefined,
  name: form.name.trim(),
})

export const isDatabricksConfigDirty = (
  form: DatabricksFormState,
  initialConfig: DatabricksConfig | undefined,
): boolean => {
  const initial = { ...DATABRICKS_DEFAULTS, ...initialConfig }
  const config = buildDatabricksConfig(form)
  return (
    config.host !== initial.host ||
    config.workspace_id !== initial.workspace_id ||
    config.region !== initial.region ||
    config.warehouse_id !== initial.warehouse_id ||
    config.catalog !== initial.catalog ||
    config.schema !== initial.schema ||
    !hasNoCredentials(form)
  )
}
