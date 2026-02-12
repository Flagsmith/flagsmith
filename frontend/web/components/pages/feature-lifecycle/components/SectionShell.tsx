import React, { FC, ReactNode, useCallback } from 'react'
import ProjectFeatureRow from 'components/feature-summary/ProjectFeatureRow'
import LifecycleFiltersHeader from './LifecycleFiltersHeader'
import type { ProjectFlag } from 'common/types/responses'
import type { FilterState } from 'common/types/featureFilters'
import type { Pagination } from 'components/pages/feature-lifecycle/types'

type SectionShellProps = {
  id: string
  projectId: number
  items: ProjectFlag[]
  paging: Pagination
  isLoading: boolean
  error: unknown
  filters: FilterState
  hasFilters: boolean
  onFilterChange: (updates: Partial<FilterState>) => void
  onClearFilters: () => void
  emptyLabel: string
  nextPage: () => void
  prevPage: () => void
  goToPage: (page: number) => void
  header?: ReactNode
  isSelected?: (flag: ProjectFlag) => boolean
  onSelect?: (flag: ProjectFlag) => void
  renderActions?: (flag: ProjectFlag) => ReactNode
}

const SectionShell: FC<SectionShellProps> = ({
  emptyLabel,
  error,
  filters,
  goToPage,
  hasFilters,
  header,
  id,
  isLoading,
  isSelected,
  items,
  nextPage,
  onClearFilters,
  onFilterChange,
  onSelect,
  paging,
  prevPage,
  projectId,
  renderActions,
}) => {
  const renderHeader = useCallback(
    () => (
      <LifecycleFiltersHeader
        projectId={projectId}
        filters={filters}
        hasFilters={hasFilters}
        isLoading={isLoading}
        onFilterChange={onFilterChange}
        onClearFilters={onClearFilters}
      />
    ),
    [projectId, filters, hasFilters, isLoading, onFilterChange, onClearFilters],
  )

  const renderFeatureRow = useCallback(
    (projectFlag: ProjectFlag, i: number) => (
      <ProjectFeatureRow
        key={projectFlag.id}
        projectFlag={projectFlag}
        index={i}
        isSelected={isSelected?.(projectFlag)}
        onSelect={onSelect}
        actions={renderActions?.(projectFlag)}
      />
    ),
    [isSelected, onSelect, renderActions],
  )

  if (error) {
    return (
      <div className='text-center'>
        <h4 className='mb-3'>Unable to Load Features</h4>
        <p className='text-muted mb-3'>
          We couldn&apos;t load your feature flags. This might be due to a
          network issue or a temporary server problem.
        </p>
      </div>
    )
  }

  const hasNoResults =
    !isLoading && items.length === 0 && !filters.search && !hasFilters

  if (hasNoResults) {
    return (
      <div className='text-center py-5'>
        <p className='text-muted'>{emptyLabel}</p>
      </div>
    )
  }

  return (
    <>
      {header}
      <PanelSearch
        className='no-pad overflow-visible'
        id={id}
        renderSearchWithNoResults
        itemHeight={65}
        isLoading={isLoading}
        paging={paging}
        header={renderHeader()}
        nextPage={nextPage}
        prevPage={prevPage}
        goToPage={goToPage}
        items={items}
        renderRow={renderFeatureRow}
      />
    </>
  )
}

export default SectionShell
