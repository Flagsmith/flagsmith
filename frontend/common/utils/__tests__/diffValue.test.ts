import { stringifyDiffValue } from 'common/utils/diffValue'

describe('stringifyDiffValue', () => {
  it('returns an empty string for null and undefined', () => {
    expect(stringifyDiffValue(null)).toBe('')
    expect(stringifyDiffValue(undefined)).toBe('')
  })

  it('quotes the empty string', () => {
    expect(stringifyDiffValue('')).toBe('""')
  })

  it('stringifies primitives', () => {
    expect(stringifyDiffValue('abc')).toBe('abc')
    expect(stringifyDiffValue(3)).toBe('3')
    expect(stringifyDiffValue(false)).toBe('false')
  })

  it('pretty-prints arrays of objects instead of [object Object]', () => {
    const rules = [
      { conditions: [{ operator: 'EQUAL', property: 'a', value: '1' }] },
    ]
    const result = stringifyDiffValue(rules)
    expect(result).not.toContain('[object Object]')
    expect(JSON.parse(result)).toEqual(rules)
  })
})
