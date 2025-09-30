import React from 'react'
import ClearFilters from 'components/ClearFilters'
import TableSearchFilter from 'components/tables/TableSearchFilter'
import TableTagFilter from 'components/tables/TableTagFilter'
import TableValueFilter from 'components/tables/TableValueFilter'
import TableOwnerFilter from 'components/tables/TableOwnerFilter'
import TableGroupsFilter from 'components/tables/TableGroupsFilter'
import TableFilterOptions from 'components/tables/TableFilterOptions'
import TableSortFilter from 'components/tables/TableSortFilter'
import { getViewMode, setViewMode, ViewMode } from 'common/useViewMode'
import { isEqual } from 'lodash'
import Utils from 'common/utils/utils'
import { TagStrategy } from 'common/types/responses'

type SortState = {
  label: string
  sortBy: string
  sortOrder: 'asc' | 'desc' | null
}

type FiltersValue = {
  search: string | null
  tag_strategy: TagStrategy
  tags: (number | string)[]
  showArchived: boolean
  value_search: string | null
  is_enabled: boolean | null
  owners: number[]
  group_owners: number[]
  sort: SortState
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
  is_enabled: null,
  owners: [],
  search: '',
  showArchived: false,
  sort: { label: 'Name', sortBy: 'name', sortOrder: 'asc' },
  tag_strategy: 'INTERSECTION',
  tags: [],
  value_search: '',
}

const isDefault = (v: FiltersValue) =>
  isEqual(
    {
      ...v,
      search: v.search || '',
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
            onToggleArchived={(next) => set({ showArchived: next })}
            showArchived={value.showArchived}
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
