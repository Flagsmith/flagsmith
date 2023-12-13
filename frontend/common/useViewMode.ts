import flagsmith from 'flagsmith'

export type ViewMode = 'compact' | 'normal'
export function getViewMode() {
  const viewMode = flagsmith.getTrait('view_mode')
  if (viewMode === 'compact') {
    return 'compact' as ViewMode
  }
  return 'default' as ViewMode
}
export function setViewMode(viewMode: ViewMode) {
  return flagsmith.setTrait('view_mode', viewMode)
}
