import { getWarehousePollingInterval } from 'components/pages/environment-settings/tabs/warehouse-tab/warehousePolling'

describe('getWarehousePollingInterval', () => {
  it('polls every 30s while pending_connection', () => {
    expect(getWarehousePollingInterval('pending_connection')).toBe(30000)
  })

  it('does not poll for connected', () => {
    expect(getWarehousePollingInterval('connected')).toBe(0)
  })

  it('does not poll for created', () => {
    expect(getWarehousePollingInterval('created')).toBe(0)
  })

  it('does not poll for errored', () => {
    expect(getWarehousePollingInterval('errored')).toBe(0)
  })

  it('does not poll when status is undefined', () => {
    expect(getWarehousePollingInterval(undefined)).toBe(0)
  })
})
