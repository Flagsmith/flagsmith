import { getConfigurableWarehouseTypes } from 'components/pages/environment-settings/tabs/warehouse-tab/warehouseTypes'

describe('getConfigurableWarehouseTypes', () => {
  it.each([
    [false, ['clickhouse', 'databricks']],
    [true, ['flagsmith', 'clickhouse', 'databricks']],
  ])('isSaas=%s => %j', (isSaas, expected) => {
    expect(getConfigurableWarehouseTypes(isSaas)).toEqual(expected)
  })
})
