import {
  buildSnowflakePayload,
  canTestSnowflakeConnection,
  getPrivateKeyError,
  isAccountLocator,
  isSnowflakeConfigDirty,
  isSnowflakeFormValid,
  isValidAccountIdentifier,
  isValidIdentifier,
  normaliseAccountIdentifier,
  SnowflakeFormState,
} from 'components/pages/environment-settings/tabs/warehouse-tab/snowflakeConfig'

const privateKey =
  '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASC\n-----END PRIVATE KEY-----'

const validForm: SnowflakeFormState = {
  account_identifier: 'MYORG-MYACCOUNT',
  database: 'FLAGSMITH',
  name: 'Production Snowflake',
  private_key: privateKey,
  role: 'FLAGSMITH_ROLE',
  schema: 'FLAGSMITH_EXP',
  user: 'FLAGSMITH_SERVICE',
  warehouse: 'FLAGSMITH_WH',
}

const storedConfig = {
  account_identifier: 'MYORG-MYACCOUNT',
  database: 'FLAGSMITH',
  role: 'FLAGSMITH_ROLE',
  schema: 'FLAGSMITH_EXP',
  user: 'FLAGSMITH_SERVICE',
  warehouse: 'FLAGSMITH_WH',
}

describe('normaliseAccountIdentifier', () => {
  it.each([
    ['  myorg-myaccount  ', 'MYORG-MYACCOUNT'],
    ['https://myorg-myaccount.snowflakecomputing.com', 'MYORG-MYACCOUNT'],
    [
      'HTTPS://MyOrg-My_Account.SnowflakeComputing.com/console?x=1#y',
      'MYORG-MY_ACCOUNT',
    ],
    ['xy12345.eu-west-1.snowflakecomputing.com', 'XY12345.EU-WEST-1'],
  ])('normalises %p to %p', (input, expected) => {
    expect(normaliseAccountIdentifier(input)).toBe(expected)
  })
})

describe('isValidAccountIdentifier', () => {
  it.each([
    'MYORG-MYACCOUNT',
    'myorg-my_account',
    'https://myorg-my-account.snowflakecomputing.com/',
  ])('accepts %p', (value) => {
    expect(isValidAccountIdentifier(value)).toBe(true)
  })

  it.each([
    '',
    'myaccount',
    '-myaccount',
    'my_org-myaccount',
    'xy12345.eu-west-1',
  ])('rejects %p', (value) => {
    expect(isValidAccountIdentifier(value)).toBe(false)
  })
})

describe('isAccountLocator', () => {
  it.each([
    ['xy12345.eu-west-1', true],
    ['https://xy12345.eu-west-1.aws.snowflakecomputing.com', true],
    ['https://myorg-myaccount.snowflakecomputing.com', false],
    ['https://app.snowflake.com/myorg/myaccount/#/homepage', false],
  ])('%p returns %p', (value, expected) => {
    expect(isAccountLocator(value)).toBe(expected)
  })
})

describe('isValidIdentifier', () => {
  it.each(['FLAGSMITH_WH', 'flagsmith', '_PRIVATE', 'COST$CENTRE', 'A1'])(
    'accepts %p',
    (value) => {
      expect(isValidIdentifier(value)).toBe(true)
    },
  )

  it.each(['', '1WH', 'MY-WH', 'A.B', 'MY WH'])('rejects %p', (value) => {
    expect(isValidIdentifier(value)).toBe(false)
  })
})

describe('getPrivateKeyError', () => {
  it.each([
    privateKey,
    `\n  ${privateKey}\n`,
    '-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----',
  ])('accepts %p', (value) => {
    expect(getPrivateKeyError(value)).toBeNull()
  })

  it.each([
    ['-----BEGIN ENCRYPTED PRIVATE KEY-----\nabc', /passphrase-protected/],
    ['-----BEGIN PUBLIC KEY-----\nabc', /public key/],
    ['MIIEvQIBADANBgkqhkiG9w0BAQEFAASC', /whole private key/],
    ['-----BEGIN PRIVATE KEY-----\nabc', /whole private key/],
  ])('rejects %p', (value, expected) => {
    expect(getPrivateKeyError(value)).toMatch(expected)
  })
})

describe('isSnowflakeFormValid', () => {
  it('accepts a complete form on create', () => {
    expect(isSnowflakeFormValid(validForm, false)).toBe(true)
  })

  it.each([
    'name',
    'account_identifier',
    'warehouse',
    'database',
    'schema',
    'role',
    'user',
    'private_key',
  ] as const)('rejects a form with empty %s on create', (field) => {
    expect(isSnowflakeFormValid({ ...validForm, [field]: '' }, false)).toBe(
      false,
    )
  })

  it('allows an empty private key on edit', () => {
    expect(isSnowflakeFormValid({ ...validForm, private_key: '' }, true)).toBe(
      true,
    )
  })

  it('rejects an invalid private key on edit', () => {
    expect(
      isSnowflakeFormValid({ ...validForm, private_key: 'not a key' }, true),
    ).toBe(false)
  })
})

describe('canTestSnowflakeConnection', () => {
  it('accepts a complete form regardless of name', () => {
    expect(canTestSnowflakeConnection({ ...validForm, name: '' })).toBe(true)
  })

  it.each([
    ['account_identifier', ''],
    ['private_key', ''],
    ['private_key', '-----BEGIN PUBLIC KEY-----\nabc'],
  ] as const)('rejects a form with %s %p', (field, value) => {
    expect(canTestSnowflakeConnection({ ...validForm, [field]: value })).toBe(
      false,
    )
  })
})

describe('buildSnowflakePayload', () => {
  it('builds a normalised payload with credentials', () => {
    expect(
      buildSnowflakePayload({
        account_identifier: 'https://myorg-myaccount.snowflakecomputing.com/',
        database: ' flagsmith ',
        name: ' Production Snowflake ',
        private_key: `\n${privateKey}\n`,
        role: 'flagsmith_role',
        schema: 'flagsmith_exp',
        user: ' flagsmith_service',
        warehouse: 'flagsmith_wh ',
      }),
    ).toEqual({
      config: storedConfig,
      credentials: { private_key: privateKey },
      name: 'Production Snowflake',
    })
  })

  it('omits credentials when no private key is entered', () => {
    expect(
      buildSnowflakePayload({ ...validForm, private_key: ' ' }).credentials,
    ).toBeUndefined()
  })
})

describe('isSnowflakeConfigDirty', () => {
  const pristine = { ...validForm, private_key: '' }

  it('is clean when nothing changed', () => {
    expect(isSnowflakeConfigDirty(pristine, storedConfig)).toBe(false)
  })

  it('is clean when only the formatting differs from the stored config', () => {
    expect(
      isSnowflakeConfigDirty(
        { ...pristine, schema: ' flagsmith_exp ', warehouse: 'flagsmith_wh' },
        storedConfig,
      ),
    ).toBe(false)
  })

  it.each([
    ['warehouse', 'OTHER_WH'],
    ['role', 'OTHER_ROLE'],
    ['private_key', privateKey],
  ] as const)('is dirty when %s changes', (field, value) => {
    expect(
      isSnowflakeConfigDirty({ ...pristine, [field]: value }, storedConfig),
    ).toBe(true)
  })
})
