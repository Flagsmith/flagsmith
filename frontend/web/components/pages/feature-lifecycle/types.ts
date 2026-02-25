import type { ProjectFlag } from 'common/types/responses'

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

export type EvaluationResult = {
  featureId: number
  environmentId: string
  hasEvaluations: boolean
}

export type LifecycleData = {
  newFlags: ProjectFlag[]
  liveFlags: ProjectFlag[]
  permanentFlags: ProjectFlag[]
  staleFlags: ProjectFlag[]
  staleNoCodeFlags: ProjectFlag[]
  counts: LifecycleCounts
  isLoading: boolean
  error: unknown
  refetch: () => void
}
