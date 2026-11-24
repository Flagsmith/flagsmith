const { healthCheck } = require('../health')

describe('healthCheck', () => {
  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('returns OK without logging the probe', () => {
    const log = jest.spyOn(console, 'log').mockImplementation(() => {})
    const debug = jest.spyOn(console, 'debug').mockImplementation(() => {})
    const res = { send: jest.fn() }

    healthCheck({} as never, res as never)

    expect(res.send).toHaveBeenCalledWith('OK')
    expect(log).not.toHaveBeenCalled()
    expect(debug).not.toHaveBeenCalled()
  })
})
