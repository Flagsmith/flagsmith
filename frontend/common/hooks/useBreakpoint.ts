import { useEffect, useState } from 'react'

// Bootstrap breakpoints, so components agree with the media queries in SCSS.
// Add a size when a component needs it.
export const BREAKPOINT_QUERIES = {
  isPhone: '(max-width: 767.98px)', // below md
} as const

export type Breakpoint = keyof typeof BREAKPOINT_QUERIES

export const matchesBreakpoint = (breakpoint: Breakpoint): boolean =>
  typeof window !== 'undefined' &&
  !!window.matchMedia?.(BREAKPOINT_QUERIES[breakpoint]).matches

export const useBreakpoint = (breakpoint: Breakpoint): boolean => {
  const [isMatch, setIsMatch] = useState(() => matchesBreakpoint(breakpoint))

  useEffect(() => {
    const list = window.matchMedia?.(BREAKPOINT_QUERIES[breakpoint])
    if (!list) return
    const onChange = () => setIsMatch(list.matches)
    onChange()
    list.addEventListener('change', onChange)
    return () => list.removeEventListener('change', onChange)
  }, [breakpoint])

  return isMatch
}
