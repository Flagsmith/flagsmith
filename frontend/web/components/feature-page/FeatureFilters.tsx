import React from 'react'
import ClearFilters from 'components/ClearFilters'
import TableSearchFilter from 'components/tables/TableSearchFilter'
import TableTagFilter from 'components/tables/TableTagFilter'
import TableValueFilter from 'components/tables/TableValueFilter'
import TableOwnerFilter from 'components/tables/TableOwnerFilter'
import TableGroupsFilter from 'components/tables/TableGroupsFilter'
import TableFilterOptions from 'components/tables/TableFilterOptions'
import TableSortFilter, { SortValue } from 'components/tables/TableSortFilter'
import { getViewMode, setViewMode, ViewMode } from 'common/useViewMode'
import { isEqual } from 'lodash'
import Utils from 'common/utils/utils'
import { TagStrategy } from 'common/types/responses'
import Format from 'common/utils/format'

export type FiltersValue = {
  search: string | null
  releasePipelines: number[]
  page: number
  tag_strategy: TagStrategy
  tags: (number | string)[]
  is_archived: boolean
  value_search: string | null
  is_enabled: boolean | null
  owners: number[]
  group_owners: number[]
  sort: SortValue
}

type Props = {
  value: FiltersValue
  onChange: (next: FiltersValue) => void
  projectId: string | number
  orgId?: number
  isLoading?: boolean
}

const DEFAULTS: FiltersValue = {
  group_owners: [],
  is_archived: false,
  is_enabled: null,
  owners: [],
  page: 1,
  releasePipelines: [],
  search: '',
  sort: { label: 'Name', sortBy: 'name', sortOrder: 'asc' },
  tag_strategy: 'INTERSECTION',
  tags: [],
  value_search: '',
}

const sortToHeader = (s: any) => {
  if (!s) return DEFAULTS.sort
  if ('sortBy' in s) return s
  return {
    label: s.label || DEFAULTS.sort.label,
    sortBy: s.value || DEFAULTS.sort.sortBy,
    sortOrder: DEFAULTS.sort.sortOrder,
  } as FiltersValue['sort']
}

// Converts filters to url params, excluding ones that are already default
export function getURLParamsFromFilters(f: FiltersValue) {
  const existing = Utils.fromParam() as Record<string, string | undefined>

  return {
    ...existing,
    group_owners: f.group_owners?.length ? f.group_owners.join(',') : undefined,
    is_archived: f.is_archived ? 'true' : undefined,
    is_enabled:
      f.is_enabled === null ? undefined : f.is_enabled ? 'true' : 'false',
    owners: f.owners?.length ? f.owners.join(',') : undefined,
    page: f.page !== DEFAULTS.page ? String(f.page) : undefined,
    search: f.search || undefined,
    tag_strategy:
      f.tag_strategy !== DEFAULTS.tag_strategy
        ? String(f.tag_strategy)
        : undefined,
    tags: f.tags?.length ? f.tags.join(',') : undefined,
    value_search: f.value_search || undefined,
  }
}
// Gets expected filters from URL parameters
export const getFiltersFromURLParams = (
  params: Record<string, string | undefined>,
) => {
  return {
    group_owners:
      typeof params.group_owners === 'string'
        ? params.group_owners.split(',').map((v) => parseInt(v))
        : [],
    is_archived: params.is_archived === 'true',
    is_enabled:
      params.is_enabled === 'true'
        ? true
        : params.is_enabled === 'false'
        ? false
        : null,
    owners:
      typeof params.owners === 'string'
        ? params.owners.split(',').map((v) => parseInt(v))
        : [],
    page: params.page ? parseInt(params.page) - 1 : 1,
    releasePipelines: [],
    search: params.search || '',
    sort: {
      label: Format.camelCase(params.sortBy || 'Name'),
      sortBy: params.sortBy || 'name',
      sortOrder: params.sortOrder || 'asc',
    },
    tag_strategy: params.tag_strategy || 'INTERSECTION',
    tags:
      typeof params.tags === 'string'
        ? params.tags.split(',').map((v) => parseInt(v))
        : [],
    value_search:
      typeof params.value_search === 'string' ? params.value_search : '',
  } as FiltersValue
}

//Converts filter to api expected properties
export const getServerFilter = (f: FiltersValue) => ({
  ...f,
  group_owners: f.group_owners?.length ? f.group_owners : undefined,
  owners: f.owners.length ? f.owners : undefined,
  search: (f.search || '').trim(),
  sort: sortToHeader(f.sort),
  tags: f.tags.length ? f.tags.join(',') : undefined,
})

//Detect if the filter is default
const isDefault = (v: FiltersValue) =>
  isEqual(
    {
      ...v,
    },
    DEFAULTS,
  )

const FeatureFilters: React.FC<Props> = ({
  isLoading,
  onChange,
  orgId,
  projectId,
  value,
}) => {
  const set = (partial: Partial<FiltersValue>) =>
    onChange({ ...value, ...partial })
  const clearAll = () => onChange({ ...DEFAULTS })
  return (
    <div className='table-header d-flex align-items-center'>
      <div className='table-column flex-row flex-fill'>
        <TableSearchFilter
          onChange={(e) => set({ search: Utils.safeParseEventValue(e) })}
          value={value.search}
        />
        <div className='d-flex align-items-center py-2 py-lg-0 px-1 px-lg-0 flex-fill justify-content-lg-end'>
          {!isDefault(value) && <ClearFilters onClick={clearAll} />}
          <TableTagFilter
            isLoading={!!isLoading}
            projectId={projectId}
            className='me-4'
            tagStrategy={value.tag_strategy}
            onChangeStrategy={(tag_strategy) => set({ tag_strategy })}
            value={value.tags}
            onToggleArchived={(next) => set({ is_archived: next })}
            showArchived={value.is_archived}
            onChange={(tags) => {
              if (tags.includes('') && tags.length > 1) {
                if (!(value.tags || []).includes('')) set({ tags: [''] })
                else set({ tags: tags.filter((v) => !!v) })
              } else set({ tags })
            }}
          />
          <TableValueFilter
            className={'me-4'}
            value={{
              enabled: value.is_enabled,
              valueSearch: value.value_search,
            }}
            onChange={({ enabled, valueSearch }) =>
              set({ is_enabled: enabled, value_search: valueSearch })
            }
          />
          <TableOwnerFilter
            className={'me-4'}
            value={value.owners}
            onChange={(owners) => set({ owners })}
          />
          <TableGroupsFilter
            className={'me-4'}
            orgId={orgId}
            value={value.group_owners}
            onChange={(group_owners) => set({ group_owners })}
          />
          <TableFilterOptions
            title={'View'}
            className={'me-4'}
            value={getViewMode()}
            onChange={setViewMode as any}
            options={[
              { label: 'Default', value: 'default' as ViewMode },
              { label: 'Compact', value: 'compact' as ViewMode },
            ]}
          />
          <TableSortFilter
            isLoading={!!isLoading}
            value={value.sort}
            options={[
              { label: 'Name', value: 'name' },
              { label: 'Created Date', value: 'created_date' },
            ]}
            onChange={(sort) => set({ sort })}
          />
        </div>
      </div>
    </div>
  )
}

export default FeatureFilters
