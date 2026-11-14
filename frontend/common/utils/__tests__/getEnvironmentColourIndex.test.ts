import { getEnvironmentColourIndex } from 'common/utils/getEnvironmentColourIndex'

describe('getEnvironmentColourIndex', () => {
  // API order (creation order), as used by EnvironmentTagSelect
  const apiOrder = [
    { id: 3 }, // development
    { id: 1 }, // QA
    { id: 2 }, // production
  ]

  it('returns the index in the given list', () => {
    expect(getEnvironmentColourIndex(apiOrder, 3)).toBe(0)
    expect(getEnvironmentColourIndex(apiOrder, 1)).toBe(1)
    expect(getEnvironmentColourIndex(apiOrder, 2)).toBe(2)
  })

  it('follows the order of the list it is given', () => {
    const alphabetical = [...apiOrder].sort((a, b) => a.id - b.id)
    expect(getEnvironmentColourIndex(alphabetical, 3)).toBe(2)
  })

  it('falls back to 0 when the list is not loaded', () => {
    expect(getEnvironmentColourIndex(undefined, 1)).toBe(0)
  })

  it('falls back to 0 for an unknown or missing environment', () => {
    expect(getEnvironmentColourIndex(apiOrder, 99)).toBe(0)
    expect(getEnvironmentColourIndex(apiOrder, undefined)).toBe(0)
  })
})
