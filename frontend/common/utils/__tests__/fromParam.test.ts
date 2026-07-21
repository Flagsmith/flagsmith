// Tests for URL parameter parsing (replacement for Utils.fromParam)
// The inline implementation uses Object.fromEntries(new URLSearchParams(...))

describe('fromParam (URLSearchParams)', () => {
  const fromParam = (search: string) =>
    Object.fromEntries(new URLSearchParams(search))

  it('returns empty object for empty search string', () => {
    expect(fromParam('')).toEqual({})
  })

  it('parses a single parameter', () => {
    expect(fromParam('?tab=features')).toEqual({ tab: 'features' })
  })

  it('parses multiple parameters', () => {
    expect(fromParam('?tab=features&page=2&search=hello')).toEqual({
      page: '2',
      search: 'hello',
      tab: 'features',
    })
  })

  it('decodes encoded characters', () => {
    expect(fromParam('?name=hello%20world&q=a%26b')).toEqual({
      name: 'hello world',
      q: 'a&b',
    })
  })

  it('handles parameters without values', () => {
    expect(fromParam('?flag=')).toEqual({ flag: '' })
  })

  it('works without leading question mark', () => {
    expect(fromParam('tab=settings')).toEqual({ tab: 'settings' })
  })
})
