import flagsmith from 'flagsmith'

export type ViewMode = 'compact' | 'default' | 'release-manager' | 'executive' | 'dev'
export function getViewMode() {
  const viewMode = flagsmith.getTrait('view_mode')
  if (viewMode === 'compact' || viewMode === 'release-manager' || viewMode === 'executive' || viewMode === 'dev') {
    return viewMode as ViewMode
  }
  return 'default' as ViewMode
}
export function setViewMode(viewMode: ViewMode) {
  return flagsmith.setTrait('view_mode', viewMode)
}
