import { isPendingAuthorisation } from 'common/utils/pendingAuthorisation'

describe('isPendingAuthorisation', () => {
  it('matches a consent request with its query', () => {
    expect(
      isPendingAuthorisation(
        '/oauth/authorize?client_id=flagsmith-cli&scope=admin-api&state=abc',
      ),
    ).toBe(true)
  })

  it('matches the trailing-slash form the CLI is sent to', () => {
    expect(isPendingAuthorisation('/oauth/authorize/?client_id=x')).toBe(true)
  })

  it('matches the bare path', () => {
    expect(isPendingAuthorisation('/oauth/authorize')).toBe(true)
  })

  it('does not match an identity provider callback', () => {
    expect(isPendingAuthorisation('/oauth/google?code=abc')).toBe(false)
  })

  it('does not match another page', () => {
    expect(isPendingAuthorisation('/project/1/environment/abc/features')).toBe(
      false,
    )
  })

  it('does not match an absolute url wearing the path', () => {
    expect(isPendingAuthorisation('https://evil.example/oauth/authorize')).toBe(
      false,
    )
  })

  it('is false when there is no redirect', () => {
    expect(isPendingAuthorisation(undefined)).toBe(false)
    expect(isPendingAuthorisation(null)).toBe(false)
    expect(isPendingAuthorisation('')).toBe(false)
  })
})
