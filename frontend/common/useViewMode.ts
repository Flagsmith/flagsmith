import flagsmith from 'flagsmith'
import { useState, useCallback } from 'react'

export type ViewMode = 'compact' | 'default' | 'release-manager' | 'executive' | 'dev'
export function getViewMode() {
  const viewMode = flagsmith.getTrait('view_mode')
  if (viewMode === 'compact' || viewMode === 'release-manager' || viewMode === 'executive' || viewMode === 'dev') {
    return viewMode as ViewMode
  }
  return 'default'
}

export function setViewMode(viewMode: ViewMode) {
  return flagsmith.setTrait('view_mode', viewMode)
}

/**
 * Hook for managing view mode with optimistic UI updates.
 * Updates state immediately for instant feedback, then persists to Flagsmith in background.
 */
export function useViewMode() {
  const [viewMode, setViewModeState] = useState<ViewMode>(getViewMode)

  const updateViewMode = useCallback((value: ViewMode) => {
    setViewModeState(value) // Optimistic update - instant UI change
    setViewMode(value) // Persist to Flagsmith trait in background
  }, [])

  return {
    isCompact: viewMode === 'compact',
    setViewMode: updateViewMode,
    viewMode,
  }
}
