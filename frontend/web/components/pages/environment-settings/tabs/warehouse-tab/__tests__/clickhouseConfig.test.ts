import {
  buildClickHousePayload,
  canTestClickHouseConnection,
  ClickHouseFormState,
  isClickHouseConfigDirty,
  isClickHouseFormValid,
  isValidPort,
} from 'components/pages/environment-settings/tabs/warehouse-tab/clickhouseConfig'

const validForm: ClickHouseFormState = {
  database: 'flagsmith',
  host: 'ch.example.com',
  name: 'Production ClickHouse',
  password: 'hunter2',
  port: '9440',
  secure: true,
  username: 'default',
}

describe('isValidPort', () => {
  it('accepts ports within 1-65535', () => {
    expect(isValidPort('1')).toBe(true)
    expect(isValidPort('9440')).toBe(true)
    expect(isValidPort('65535')).toBe(true)
  })

  it('rejects out-of-range or non-numeric ports', () => {
    expect(isValidPort('0')).toBe(false)
    expect(isValidPort('65536')).toBe(false)
    expect(isValidPort('abc')).toBe(false)
    expect(isValidPort('94.4')).toBe(false)
    expect(isValidPort('')).toBe(false)
  })
})

describe('isClickHouseFormValid', () => {
  it('accepts a complete form on create', () => {
    expect(isClickHouseFormValid(validForm, false)).toBe(true)
  })

  it.each(['name', 'host', 'database', 'username', 'password'] as const)(
    'rejects a form with empty %s on create',
    (field) => {
      expect(isClickHouseFormValid({ ...validForm, [field]: '' }, false)).toBe(
        false,
      )
    },
  )

  it('allows an empty password on edit (keeps the stored one)', () => {
    expect(isClickHouseFormValid({ ...validForm, password: '' }, true)).toBe(
      true,
    )
  })
})

describe('canTestClickHouseConnection', () => {
  it('accepts a complete form regardless of name', () => {
    expect(canTestClickHouseConnection({ ...validForm, name: '' })).toBe(true)
  })

  it.each(['host', 'port', 'database', 'username', 'password'] as const)(
    'rejects a form with empty %s',
    (field) => {
      expect(canTestClickHouseConnection({ ...validForm, [field]: '' })).toBe(
        false,
      )
    },
  )
})

describe('isClickHouseConfigDirty', () => {
  const initialConfig = {
    database: 'flagsmith',
    host: 'ch.example.com',
    port: 9440,
    secure: true,
    username: 'default',
  }

  it('is clean when the form matches the stored config with a blank password', () => {
    expect(
      isClickHouseConfigDirty({ ...validForm, password: '' }, initialConfig),
    ).toBe(false)
  })

  it.each([
    ['port', { port: '9000' }],
    ['database', { database: 'analytics' }],
    ['username', { username: 'svc' }],
    ['secure', { secure: false }],
    ['password', { password: 'hunter2' }],
  ] as const)('is dirty when %s changes', (_, change) => {
    expect(
      isClickHouseConfigDirty(
        { ...validForm, password: '', ...change },
        initialConfig,
      ),
    ).toBe(true)
  })

  it('compares against defaults when there is no stored config', () => {
    expect(
      isClickHouseConfigDirty({ ...validForm, password: '' }, undefined),
    ).toBe(true)
  })
})

describe('buildClickHousePayload', () => {
  it('builds config with a numeric port and separates credentials', () => {
    expect(buildClickHousePayload(validForm)).toEqual({
      config: {
        database: 'flagsmith',
        host: 'ch.example.com',
        port: 9440,
        secure: true,
        username: 'default',
      },
      credentials: { password: 'hunter2' },
      name: 'Production ClickHouse',
    })
  })

  it('omits credentials when the password is blank (edit keeps stored)', () => {
    expect(
      buildClickHousePayload({ ...validForm, password: '' }).credentials,
    ).toBeUndefined()
  })
})
