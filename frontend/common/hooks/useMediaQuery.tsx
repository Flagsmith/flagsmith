import { useEffect, useState } from 'react'

export default function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window !== 'undefined' ? window.matchMedia(query).matches : false,
  )

  useEffect(() => {
    const mediaQuery = window.matchMedia(query)

    const updateMatch = () => setMatches(mediaQuery.matches)
    mediaQuery.addEventListener('change', updateMatch)

    updateMatch()

    return () => mediaQuery.removeEventListener('change', updateMatch)
  }, [query])

  return matches
}
