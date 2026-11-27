import { SnowflakeConfig } from 'common/types/responses'

export const SNOWFLAKE_DEFAULTS: SnowflakeConfig = {
  account_identifier: '',
  database: 'FLAGSMITH',
  role: 'FLAGSMITH_ROLE',
  schema: 'FLAGSMITH_EXP',
  user: 'FLAGSMITH_SERVICE',
  warehouse: 'FLAGSMITH_WH',
}

const ACCOUNT_IDENTIFIER = /^[A-Za-z0-9]+-[A-Za-z0-9_-]+$/
const IDENTIFIER = /^[A-Za-z_][A-Za-z0-9_$]*$/
const PRIVATE_KEY =
  /-----BEGIN (RSA )?PRIVATE KEY-----[\s\S]+-----END (RSA )?PRIVATE KEY-----/

export type SnowflakeFormState = {
  name: string
  account_identifier: string
  warehouse: string
  database: string
  schema: string
  role: string
  user: string
  private_key: string
}

export type SnowflakeCredentials = {
  private_key: string
}

export type SnowflakeFormData = {
  name: string
  config: SnowflakeConfig
  credentials?: SnowflakeCredentials
}

export const normaliseAccountIdentifier = (accountIdentifier: string): string =>
  accountIdentifier
    .trim()
    .replace(/^[a-z][a-z0-9+.-]*:\/\//i, '')
    .split(/[/?#]/)[0]
    .replace(/\.snowflakecomputing\.com$/i, '')
    .toUpperCase()

export const normaliseIdentifier = (value: string): string =>
  value.trim().toUpperCase()

export const isValidAccountIdentifier = (accountIdentifier: string): boolean =>
  ACCOUNT_IDENTIFIER.test(normaliseAccountIdentifier(accountIdentifier))

export const isAccountLocator = (accountIdentifier: string): boolean => {
  const normalised = normaliseAccountIdentifier(accountIdentifier)
  return normalised.includes('.') && !normalised.endsWith('.COM')
}

export const isValidIdentifier = (value: string): boolean =>
  IDENTIFIER.test(value.trim())

export const getPrivateKeyError = (privateKey: string): string | null => {
  const value = privateKey.trim()
  if (value.startsWith('-----BEGIN ENCRYPTED PRIVATE KEY-----')) {
    return 'This key is passphrase-protected. Generate one without a passphrase (-nocrypt), as in step 1.'
  }
  if (value.startsWith('-----BEGIN PUBLIC KEY-----')) {
    return 'This is the public key. Paste the contents of the private key file, flagsmith_key.p8.'
  }
  if (!PRIVATE_KEY.test(value)) {
    return 'Paste the whole private key, including the BEGIN and END lines.'
  }
  return null
}

export const isValidPrivateKey = (privateKey: string): boolean =>
  !getPrivateKeyError(privateKey)

export const hasSnowflakeCredentials = (form: SnowflakeFormState): boolean =>
  !!form.private_key.trim()

const isSnowflakeConfigValid = (form: SnowflakeFormState): boolean =>
  isValidAccountIdentifier(form.account_identifier) &&
  isValidIdentifier(form.warehouse) &&
  isValidIdentifier(form.database) &&
  isValidIdentifier(form.schema) &&
  isValidIdentifier(form.role) &&
  isValidIdentifier(form.user)

export const isSnowflakeFormValid = (
  form: SnowflakeFormState,
  isEdit: boolean,
): boolean =>
  !!form.name.trim() &&
  isSnowflakeConfigValid(form) &&
  (hasSnowflakeCredentials(form) ? isValidPrivateKey(form.private_key) : isEdit)

export const canTestSnowflakeConnection = (form: SnowflakeFormState): boolean =>
  isSnowflakeConfigValid(form) &&
  hasSnowflakeCredentials(form) &&
  isValidPrivateKey(form.private_key)

const buildSnowflakeConfig = (form: SnowflakeFormState): SnowflakeConfig => ({
  account_identifier: normaliseAccountIdentifier(form.account_identifier),
  database: normaliseIdentifier(form.database),
  role: normaliseIdentifier(form.role),
  schema: normaliseIdentifier(form.schema),
  user: normaliseIdentifier(form.user),
  warehouse: normaliseIdentifier(form.warehouse),
})

export const buildSnowflakePayload = (
  form: SnowflakeFormState,
): SnowflakeFormData => ({
  config: buildSnowflakeConfig(form),
  credentials: hasSnowflakeCredentials(form)
    ? { private_key: form.private_key.trim() }
    : undefined,
  name: form.name.trim(),
})

export const isSnowflakeConfigDirty = (
  form: SnowflakeFormState,
  initialConfig: SnowflakeConfig | undefined,
): boolean => {
  const initial = { ...SNOWFLAKE_DEFAULTS, ...initialConfig }
  const config = buildSnowflakeConfig(form)
  return (
    (Object.keys(SNOWFLAKE_DEFAULTS) as (keyof SnowflakeConfig)[]).some(
      (key) => config[key] !== initial[key],
    ) || hasSnowflakeCredentials(form)
  )
}
