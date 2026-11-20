import {
  BREAKPOINT_QUERIES,
  matchesBreakpoint,
} from 'common/hooks/useBreakpoint'

// jest runs in node, so stand in for window.matchMedia.
const setMatchMedia = (
  matchMedia?: (query: string) => { matches: boolean },
) => {
  ;(global as any).window = matchMedia ? { matchMedia } : {}
}

afterEach(() => {
  delete (global as any).window
})

describe('matchesBreakpoint', () => {
  it('returns true when the breakpoint query matches', () => {
    // Given
    setMatchMedia((query) => ({
      matches: query === BREAKPOINT_QUERIES.isPhone,
    }))

    // When
    const result = matchesBreakpoint('isPhone')

    // Then
    expect(result).toBe(true)
  })

  it('returns false when the breakpoint query does not match', () => {
    // Given
    setMatchMedia(() => ({ matches: false }))

    // When
    const result = matchesBreakpoint('isPhone')

    // Then
    expect(result).toBe(false)
  })

  it('returns false when matchMedia is unavailable', () => {
    // Given
    setMatchMedia()

    // When
    const result = matchesBreakpoint('isPhone')

    // Then
    expect(result).toBe(false)
  })

  it('returns false without a window', () => {
    // Given no window

    // When
    const result = matchesBreakpoint('isPhone')

    // Then
    expect(result).toBe(false)
  })
})
