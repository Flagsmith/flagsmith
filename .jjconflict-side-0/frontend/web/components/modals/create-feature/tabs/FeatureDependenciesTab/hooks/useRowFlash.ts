import { useCallback, useEffect, useRef, useState } from 'react'

// Long enough to find the row, short enough not to linger. Must match the
// prerequisite-row-flash animation in PrerequisitesTable.scss.
const FLASH_MS = 2000

/**
 * Holds an id for a moment so the row carrying it can catch the eye, then drops
 * it. The timer lives here so no caller has to remember to clear it, which is
 * what let one add cut short the flash of the next.
 */
export const useRowFlash = () => {
  const [flashedId, setFlashedId] = useState<number | undefined>()
  const timeout = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  // The flash outlives the interaction, so it can outlive the tab.
  useEffect(() => () => clearTimeout(timeout.current), [])

  const flash = useCallback((id: number) => {
    setFlashedId(id)
    clearTimeout(timeout.current)
    timeout.current = setTimeout(() => setFlashedId(undefined), FLASH_MS)
  }, [])

  return { flash, flashedId }
}
