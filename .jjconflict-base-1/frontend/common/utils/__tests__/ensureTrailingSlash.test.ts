import { ensureTrailingSlash } from 'common/utils/ensureTrailingSlash'

describe('ensureTrailingSlash', () => {
  it('appends a slash when missing', () => {
    expect(ensureTrailingSlash('https://api.newrelic.com')).toBe(
      'https://api.newrelic.com/',
    )
  })

  it('leaves a slash-terminated url unchanged', () => {
    expect(ensureTrailingSlash('https://api.newrelic.com/')).toBe(
      'https://api.newrelic.com/',
    )
  })

  it('leaves an empty string unchanged', () => {
    expect(ensureTrailingSlash('')).toBe('')
  })
})
