import sendWarehouseTestEvent from 'components/pages/environment-settings/tabs/warehouse-tab/sendWarehouseTestEvent'

const init = jest.fn().mockResolvedValue(undefined)
const trackEvent = jest.fn()

jest.mock('@flagsmith/flagsmith/isomorphic', () => ({
  createFlagsmithInstance: () => ({ init, trackEvent }),
}))

jest.mock('common/project', () => ({
  __esModule: true,
  default: { api: 'http://localhost:8000/api/v1/' },
}))

describe('sendWarehouseTestEvent', () => {
  beforeEach(() => {
    init.mockClear()
    trackEvent.mockClear()
  })

  it('inits a per-environment instance with events enabled and no flag fetch', async () => {
    await sendWarehouseTestEvent('env-key-123')

    expect(init).toHaveBeenCalledWith(
      expect.objectContaining({
        defaultFlags: {},
        enableEvents: true,
        environmentID: 'env-key-123',
        preventFetch: true,
      }),
    )
  })

  it('tracks the test_custom_event after init', async () => {
    await sendWarehouseTestEvent('env-key-123')

    expect(trackEvent).toHaveBeenCalledWith('test_custom_event')
    expect(init).toHaveBeenCalledTimes(1)
    expect(trackEvent).toHaveBeenCalledTimes(1)
  })
})
