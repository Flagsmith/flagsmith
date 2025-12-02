import { FeatureState, ProjectFlag } from 'common/types/responses'

export type Pagination = {
  count: number
  next: string | null
  previous: string | null
  page: number
  pageSize: number
}

export type EnvironmentFlagsMap = Record<number, FeatureState>

export type UrlParams = Record<string, string | string[] | undefined>

export type FeatureFilters = {
  search?: string
  tags?: string[]
  owners?: number[]
  is_archived?: boolean
  value_search?: string
  sort_field?: string
  sort_order?: 'asc' | 'desc'
  page?: number
  is_enabled?: string
  environment?: string
  group_owners?: number[]
}

export type FeatureListProps = {
  projectId: string
  environmentId: string
  projectFlags: ProjectFlag[]
  environmentFlags: EnvironmentFlagsMap
  filters: FeatureFilters
  paging: Pagination
  hasFilters: boolean
  onFilterChange: (filters: Partial<FeatureFilters>) => void
  onToggleFlag: (
    flag: ProjectFlag,
    environmentFlags: EnvironmentFlagsMap,
  ) => Promise<void>
  onRemoveFlag: (projectFlag: ProjectFlag) => Promise<void>
  organisationId?: number
}
