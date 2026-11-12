export type AuditLogListView = 'loading' | 'empty' | 'list'

// RTK Query keeps the previous result while new filters load, so an empty
// previous result must not read as "no changes" during the load.
export const getAuditLogListView = (
  isLoading: boolean,
  itemCount: number | undefined,
): AuditLogListView => {
  if (itemCount) return 'list'
  return isLoading ? 'loading' : 'empty'
}
