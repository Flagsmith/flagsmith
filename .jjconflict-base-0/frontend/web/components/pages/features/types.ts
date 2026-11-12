import { FeatureState } from 'common/types/responses'

export type Pagination = {
  count: number
  currentPage: number
  next: string | null
  pageSize: number
  previous: string | null
}

type EnvironmentFlagsMap = Record<number, FeatureState>
