import {
  buildDatabricksPayload,
  canTestDatabricksConnection,
  DatabricksFormState,
  isDatabricksConfigDirty,
  isDatabricksFormValid,
  isValidDatabricksHost,
  getWorkspaceIdFromUrl,
  isValidIdentifier,
  isValidRegion,
  isValidWarehouseId,
  isValidWorkspaceId,
  normaliseDatabricksHost,
  normaliseWarehouseId,
} from 'components/pages/environment-settings/tabs/warehouse-tab/databricksConfig'

const validForm: DatabricksFormState = {
  catalog: 'workspace',
  client_id: 'client-id',
  client_secret: 'client-secret',
  host: 'dbc-1234.cloud.databricks.com',
  name: 'Production Databricks',
  region: 'us-east-1',
  schema: 'flagsmith_exp',
  warehouse_id: 'abc123',
  workspace_id: '1234567890123456',
}

const storedConfig = {
  catalog: 'workspace',
  host: 'dbc-1234.cloud.databricks.com',
  region: 'us-east-1',
  schema: 'flagsmith_exp',
  warehouse_id: 'abc123',
  workspace_id: '1234567890123456',
}

describe('getWorkspaceIdFromUrl', () => {
  it.each([
    [
      'https://dbc-1234.cloud.databricks.com/?o=1234567890123456',
      '1234567890123456',
    ],
    ['https://adb-1.2.azuredatabricks.net/sql/editor?x=1&o=42#tab', '42'],
    ['https://dbc-1234.cloud.databricks.com/', null],
    ['dbc-1234.cloud.databricks.com?o=abc', null],
  ])('extracts from %p: %p', (url, expected) => {
    expect(getWorkspaceIdFromUrl(url)).toBe(expected)
  })
})

describe('isValidWorkspaceId', () => {
  it.each([
    ['1234567890123456', true],
    [' 42 ', true],
    ['', false],
    ['12a4', false],
  ])('%p returns %p', (value, expected) => {
    expect(isValidWorkspaceId(value)).toBe(expected)
  })
})

describe('isValidRegion', () => {
  it.each([
    ['us-east-1', true],
    ['eastus2', true],
    ['US-Central1', true],
    ['', false],
    ['us_east_1', false],
  ])('%p returns %p', (value, expected) => {
    expect(isValidRegion(value)).toBe(expected)
  })
})

describe('normaliseDatabricksHost', () => {
  it.each([
    ['  dbc-1234.cloud.databricks.com  ', 'dbc-1234.cloud.databricks.com'],
    ['http://dbc-1234.cloud.databricks.com/', 'dbc-1234.cloud.databricks.com'],
    ['HTTPS://ADB-1.2.AzureDatabricks.net', 'adb-1.2.azuredatabricks.net'],
    ['dbc-1234.cloud.databricks.com#tab', 'dbc-1234.cloud.databricks.com'],
    [
      'https://dbc-1234.cloud.databricks.com:443/sql?o=123#x',
      'dbc-1234.cloud.databricks.com',
    ],
    ['jdbc://dbc-1234.cloud.databricks.com', 'dbc-1234.cloud.databricks.com'],
  ])('normalises %p to %p', (input, expected) => {
    expect(normaliseDatabricksHost(input)).toBe(expected)
  })
})

describe('normaliseWarehouseId', () => {
  it.each([
    [' abc123 ', 'abc123'],
    ['/sql/1.0/warehouses/abc123/', 'abc123'],
    ['', ''],
  ])('normalises %p to %p', (input, expected) => {
    expect(normaliseWarehouseId(input)).toBe(expected)
  })
})

describe('isValidDatabricksHost', () => {
  it.each([
    'dbc-1234.cloud.databricks.com',
    'adb-123.4.azuredatabricks.net',
    '123.4.gcp.databricks.com',
    'https://DBC-1234.cloud.databricks.com/?o=123',
  ])('accepts %p', (host) => {
    expect(isValidDatabricksHost(host)).toBe(true)
  })

  it.each([
    '',
    'example.com',
    'cloud.databricks.com',
    'dbc_1.cloud.databricks.com',
    'dbc.cloud.databricks.com.evil.com',
  ])('rejects %p', (host) => {
    expect(isValidDatabricksHost(host)).toBe(false)
  })
})

describe('isValidWarehouseId', () => {
  it.each(['abc123', '/sql/1.0/warehouses/abc123'])('accepts %p', (id) => {
    expect(isValidWarehouseId(id)).toBe(true)
  })

  it.each(['', 'abc-123', 'abc_123'])('rejects %p', (id) => {
    expect(isValidWarehouseId(id)).toBe(false)
  })
})

describe('isValidIdentifier', () => {
  it.each(['workspace', 'flagsmith_exp', 'Main_2'])('accepts %p', (value) => {
    expect(isValidIdentifier(value)).toBe(true)
  })

  it.each(['', 'my-catalog', 'a.b'])('rejects %p', (value) => {
    expect(isValidIdentifier(value)).toBe(false)
  })
})

describe('isDatabricksFormValid', () => {
  it('accepts a complete form on create', () => {
    expect(isDatabricksFormValid(validForm, false)).toBe(true)
  })

  it.each([
    'name',
    'host',
    'workspace_id',
    'region',
    'warehouse_id',
    'catalog',
    'schema',
    'client_id',
    'client_secret',
  ] as const)('rejects a form with empty %s on create', (field) => {
    expect(isDatabricksFormValid({ ...validForm, [field]: '' }, false)).toBe(
      false,
    )
  })

  it('allows empty credentials on edit', () => {
    expect(
      isDatabricksFormValid(
        { ...validForm, client_id: '', client_secret: '' },
        true,
      ),
    ).toBe(true)
  })

  it.each(['client_id', 'client_secret'] as const)(
    'rejects only one credential (%s empty) on edit',
    (field) => {
      expect(isDatabricksFormValid({ ...validForm, [field]: '' }, true)).toBe(
        false,
      )
    },
  )
})

describe('canTestDatabricksConnection', () => {
  it('accepts a complete form regardless of name', () => {
    expect(canTestDatabricksConnection({ ...validForm, name: '' })).toBe(true)
  })

  it.each(['host', 'client_secret'] as const)(
    'rejects a form with empty %s',
    (field) => {
      expect(canTestDatabricksConnection({ ...validForm, [field]: '' })).toBe(
        false,
      )
    },
  )
})

describe('buildDatabricksPayload', () => {
  it('builds a normalised payload with credentials', () => {
    expect(
      buildDatabricksPayload({
        ...validForm,
        catalog: ' workspace ',
        client_id: ' client-id ',
        host: 'https://DBC-1234.cloud.databricks.com/',
        name: ' Production Databricks ',
        region: ' US-East-1 ',
        warehouse_id: '/sql/1.0/warehouses/abc123',
        workspace_id: ' 1234567890123456 ',
      }),
    ).toEqual({
      config: storedConfig,
      credentials: { client_id: 'client-id', client_secret: 'client-secret' },
      name: 'Production Databricks',
    })
  })

  it('omits credentials when they are not both present', () => {
    expect(
      buildDatabricksPayload({ ...validForm, client_secret: '' }).credentials,
    ).toBeUndefined()
  })
})

describe('isDatabricksConfigDirty', () => {
  const pristine = { ...validForm, client_id: '', client_secret: '' }

  it('is clean when nothing changed', () => {
    expect(isDatabricksConfigDirty(pristine, storedConfig)).toBe(false)
  })

  it('is clean when only the formatting differs from the stored config', () => {
    expect(
      isDatabricksConfigDirty(
        {
          ...pristine,
          region: 'US-EAST-1',
          warehouse_id: '/sql/1.0/warehouses/abc123',
        },
        storedConfig,
      ),
    ).toBe(false)
  })

  it.each([
    ['workspace_id', '999'],
    ['catalog', 'other'],
    ['client_secret', 'new-secret'],
  ] as const)('is dirty when %s changes', (field, value) => {
    expect(
      isDatabricksConfigDirty({ ...pristine, [field]: value }, storedConfig),
    ).toBe(true)
  })
})
