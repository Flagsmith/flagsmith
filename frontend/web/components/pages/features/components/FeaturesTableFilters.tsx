import React, { FC } from 'react'
import TableSearchFilter from 'components/tables/TableSearchFilter'
import TableTagFilter from 'components/tables/TableTagFilter'
import TableValueFilter from 'components/tables/TableValueFilter'
import TableOwnerFilter from 'components/tables/TableOwnerFilter'
import TableGroupsFilter from 'components/tables/TableGroupsFilter'
import TableFilterOptions from 'components/tables/TableFilterOptions'
import TableSortFilter from 'components/tables/TableSortFilter'
import ClearFilters from 'components/ClearFilters'
import { getViewMode, setViewMode } from 'common/useViewMode'
import type { FilterState } from 'common/types/featureFilters'

const VIEW_MODE_OPTIONS = [
  {
    label: 'Default',
    value: 'default',
  },
  {
    label: 'Compact',
    value: 'compact',
  },
]

const SORT_OPTIONS = [
  {
    label: 'Name',
    value: 'name',
  },
  {
    label: 'Created Date',
    value: 'created_date',
  },
]

type FeaturesTableFiltersProps = {
  projectId: number
  filters: FilterState
  hasFilters: boolean
  isLoading?: boolean
  orgId?: number
  onFilterChange: (updates: Partial<FilterState>) => void
  onClearFilters: () => void
}

export const FeaturesTableFilters: FC<FeaturesTableFiltersProps> = ({
  filters,
  hasFilters,
  isLoading,
  onClearFilters,
  onFilterChange,
  orgId,
  projectId,
}) => {
  const {
    group_owners: groupOwners,
    is_enabled: isEnabled,
    owners,
    search,
    showArchived,
    sort,
    tag_strategy: tagStrategy,
    tags,
    value_search: valueSearch,
  } = filters

  // Handle empty tag ('') as mutually exclusive with other tags
  const handleTagsChange = (newTags: (number | string)[]) => {
    if (newTags.includes('') && newTags.length > 1) {
      if (!tags.includes('')) {
        // User just selected empty tag - make it exclusive
        onFilterChange({ tags: [''] })
      } else {
        // Empty tag was already selected - remove it to allow other tags
        onFilterChange({ tags: newTags.filter((v) => !!v) })
      }
    } else {
      onFilterChange({ tags: newTags })
    }
  }

  const handleToggleArchivedFilter = (value: boolean) => {
    if (value !== showArchived) {
      onFilterChange({ showArchived: !showArchived })
    }
  }

  const handleValueFilterChange = ({
    enabled,
    valueSearch,
  }: {
    enabled: boolean | null
    valueSearch: string | null
  }) => {
    onFilterChange({
      is_enabled: enabled,
      value_search: valueSearch || '',
    })
  }

  return (
    <Row className='table-header'>
      <div className='table-column flex-row flex-fill'>
        <TableSearchFilter
          onChange={(v) => onFilterChange({ search: v || null })}
          value={search}
        />
        <Row className='flex-row py-2 py-lg-0 px-1 px-lg-0 flex-fill justify-content-lg-end'>
          {hasFilters && <ClearFilters onClick={onClearFilters} />}
          <TableTagFilter
            isLoading={isLoading || false}
            projectId={projectId}
            className='me-4'
            tagStrategy={tagStrategy}
            onChangeStrategy={(tag_strategy) =>
              onFilterChange({ tag_strategy })
            }
            value={tags}
            onToggleArchived={handleToggleArchivedFilter}
            showArchived={showArchived}
            onChange={handleTagsChange}
          />
          <TableValueFilter
            className='me-4'
            value={{
              enabled: isEnabled,
              valueSearch: valueSearch,
            }}
            onChange={handleValueFilterChange}
          />
          <TableOwnerFilter
            className='me-4'
            value={owners}
            onChange={(owners) => onFilterChange({ owners })}
          />
          <TableGroupsFilter
            className='me-4'
            orgId={orgId?.toString()}
            value={groupOwners}
            onChange={(group_owners) => onFilterChange({ group_owners })}
          />
          <TableFilterOptions
            title={'View'}
            className='me-4'
            value={getViewMode()}
            onChange={(value) => {
              if (value === 'default' || value === 'compact') {
                setViewMode(value)
              }
            }}
            options={VIEW_MODE_OPTIONS}
          />
          <TableSortFilter
            isLoading={!!isLoading}
            value={sort}
            options={SORT_OPTIONS}
            onChange={(sort) => onFilterChange({ sort })}
          />
        </Row>
      </div>
    </Row>
  )
}
