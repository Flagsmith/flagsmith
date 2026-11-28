import { IncomingMessage, ServerResponse } from 'http'
import { Socket } from 'net'
import securityHeadersMiddleware from '../security-headers-middleware'

describe('securityHeadersMiddleware', () => {
  it('protects responses against framing, content sniffing, referrer leaks and server fingerprinting', () => {
    // Given
    const req = new IncomingMessage(new Socket())
    const res = new ServerResponse(req)
    res.setHeader('X-Powered-By', 'Express')
    const next = jest.fn()

    // When
    securityHeadersMiddleware.forEach((middleware) =>
      middleware(req, res, next),
    )

    // Then
    expect(res.getHeaders()).toEqual({
      'content-security-policy': "frame-ancestors 'none'",
      'referrer-policy': 'strict-origin-when-cross-origin',
      'x-content-type-options': 'nosniff',
      'x-frame-options': 'DENY',
    })
    expect(next).toHaveBeenCalledTimes(securityHeadersMiddleware.length)
  })
})
