export type Section =
  | 'new'
  | 'live'
  | 'permanent'
  | 'stale'
  | 'monitor'
  | 'remove'

export type Pagination = {
  count: number
  currentPage: number
  next: string | null
  pageSize: number
  previous: string | null
}

export type LifecycleCounts = Partial<Record<Section, number>>
