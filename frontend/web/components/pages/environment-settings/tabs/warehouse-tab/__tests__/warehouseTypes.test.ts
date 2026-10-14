import { getConfigurableWarehouseTypes } from 'components/pages/environment-settings/tabs/warehouse-tab/warehouseTypes'

describe('getConfigurableWarehouseTypes', () => {
  it('does not offer the managed warehouse on self-hosted', () => {
    expect(
      getConfigurableWarehouseTypes({
        clickhouseEnabled: true,
        databricksEnabled: false,
        isSaas: false,
      }),
    ).toEqual(['clickhouse'])
  })

  it('offers the managed warehouse first on SaaS', () => {
    expect(
      getConfigurableWarehouseTypes({
        clickhouseEnabled: true,
        databricksEnabled: true,
        isSaas: true,
      }),
    ).toEqual(['flagsmith', 'clickhouse', 'databricks'])
  })
})
