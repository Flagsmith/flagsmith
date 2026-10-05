import { useCallback, useEffect, useRef, useState } from 'react'

// Long enough to find the row, short enough not to linger. Must match the
// prerequisite-row-highlight animation in PrerequisitesTable.scss.
const HIGHLIGHT_MS = 2000

/**
 * Marks the row a write just produced, and unmarks it on its own. The timer is
 * held here so no caller has to remember to clear it, which is what let one add
 * cut short the highlight of the next.
 */
export const useRowHighlight = () => {
  const [highlightedId, setHighlightedId] = useState<number | undefined>()
  const timeout = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  // The highlight outlives the interaction, so it can outlive the tab.
  useEffect(() => () => clearTimeout(timeout.current), [])

  const highlight = useCallback((id: number) => {
    setHighlightedId(id)
    clearTimeout(timeout.current)
    timeout.current = setTimeout(
      () => setHighlightedId(undefined),
      HIGHLIGHT_MS,
    )
  }, [])

  return { highlight, highlightedId }
}
