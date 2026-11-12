import {
  buildPostgresPayload,
  canTestPostgresConnection,
  isPostgresConfigDirty,
  isPostgresFormValid,
  isValidPostgresHost,
  isValidPostgresSchema,
  PostgresFormState,
} from 'components/pages/environment-settings/tabs/warehouse-tab/postgresConfig'
import { PostgresConfig } from 'common/types/responses'

const validForm: PostgresFormState = {
  database: 'analytics',
  host: 'db.example.com',
  name: 'Production PostgreSQL',
  password: 'secret',
  port: '5432',
  schema: 'flagsmith_exp',
  sslmode: 'require',
  username: 'flagsmith',
}

const storedConfig: PostgresConfig = {
  database: 'analytics',
  host: 'db.example.com',
  port: 5432,
  schema: 'flagsmith_exp',
  sslmode: 'require',
  username: 'flagsmith',
}

describe('isValidPostgresHost', () => {
  it.each([
    ['db.example.com', true],
    ['2001:db8::1', true],
    ['postgres://db.example.com', false],
    ['db.example.com:5432', false],
    ['user@db.example.com', false],
    ['', false],
  ])('returns %p for %p', (host, expected) => {
    expect(isValidPostgresHost(host)).toBe(expected)
  })
})

describe('isValidPostgresSchema', () => {
  it.each([
    ['flagsmith_exp', true],
    ['FlagsmithExp', false],
    ['1exp', false],
    ['a'.repeat(64), false],
  ])('returns %p for %p', (schema, expected) => {
    expect(isValidPostgresSchema(schema)).toBe(expected)
  })
})

describe('isPostgresFormValid and canTestPostgresConnection', () => {
  it.each<[Partial<PostgresFormState>, boolean, boolean, boolean]>([
    [{}, false, true, true],
    [{ name: '' }, false, false, true],
    [{ password: '' }, false, false, false],
    [{ password: '' }, true, true, false],
    [{ host: 'postgres://db' }, false, false, false],
    [{ host: 'postgres://db' }, true, true, true],
  ])(
    'with %j and isEdit=%p, returns valid=%p and testable=%p',
    (overrides, isEdit, isValid, isTestable) => {
      const form = { ...validForm, ...overrides }
      expect(isPostgresFormValid(form, isEdit)).toBe(isValid)
      expect(canTestPostgresConnection(form, isEdit)).toBe(isTestable)
    },
  )
})

describe('buildPostgresPayload', () => {
  it('converts the port to a number and keeps sslmode', () => {
    expect(
      buildPostgresPayload({
        ...validForm,
        port: ' 5433 ',
        sslmode: 'disable',
      }),
    ).toEqual({
      config: { ...storedConfig, port: 5433, sslmode: 'disable' },
      credentials: { password: 'secret' },
      name: 'Production PostgreSQL',
    })
  })
})

describe('isPostgresConfigDirty', () => {
  it.each<[Partial<PostgresFormState>, boolean]>([
    [{ name: 'Renamed', password: '' }, false],
    [{ password: '', port: '5433' }, true],
    [{ password: '', sslmode: 'disable' }, true],
    [{}, true],
  ])('with %j, returns %p', (overrides, expected) => {
    expect(
      isPostgresConfigDirty({ ...validForm, ...overrides }, storedConfig),
    ).toBe(expected)
  })
})
