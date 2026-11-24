import frameProtectionMiddleware from '../frame-protection-middleware'

describe('frameProtectionMiddleware', () => {
  it('sets headers that deny framing and calls next', () => {
    const res = { setHeader: jest.fn() }
    const next = jest.fn()

    frameProtectionMiddleware({}, res, next)

    expect(res.setHeader).toHaveBeenCalledWith('X-Frame-Options', 'DENY')
    expect(res.setHeader).toHaveBeenCalledWith(
      'Content-Security-Policy',
      "frame-ancestors 'none'",
    )
    expect(next).toHaveBeenCalledTimes(1)
  })
})
