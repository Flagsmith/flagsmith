import { SyntheticEvent } from 'react'

// Popovers often open from a clickable row, and the panel renders in a portal
// that React still bubbles through. Clicks on the trigger or inside the panel
// must not also reach the row
export const stopPropagation = (e: SyntheticEvent) => e.stopPropagation()
