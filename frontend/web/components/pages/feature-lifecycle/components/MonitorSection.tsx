import React, { FC } from 'react'
import SectionShell from './SectionShell'
import { useClientPagination } from 'components/pages/feature-lifecycle/hooks/useClientPagination'
import type { ProjectFlag } from 'common/types/responses'
import type { FilterState } from 'common/types/featureFilters'

type MonitorSectionProps = {
  flags: ProjectFlag[]
  isLoading: boolean
  isCheckingEvaluations: boolean
  error: unknown
  projectId: number
  filters: FilterState
  hasFilters: boolean
  onFilterChange: (updates: Partial<FilterState>) => void
  onClearFilters: () => void
}

const MonitorSection: FC<MonitorSectionProps> = ({
  error,
  filters,
  flags,
  hasFilters,
  isCheckingEvaluations,
  isLoading,
  onClearFilters,
  onFilterChange,
  projectId,
}) => {
  const { goToPage, nextPage, pageItems, paging, prevPage } =
    useClientPagination({ items: flags })

  if (isCheckingEvaluations && !isLoading) {
    return (
      <div className='text-center py-4'>
        <Loader />
        <p className='text-muted mt-2'>
          Checking evaluation data for features...
        </p>
      </div>
    )
  }

  return (
    <SectionShell
      id='monitor-list'
      projectId={projectId}
      items={pageItems}
      paging={paging}
      isLoading={isLoading}
      error={error}
      filters={filters}
      hasFilters={hasFilters}
      onFilterChange={onFilterChange}
      onClearFilters={onClearFilters}
      emptyLabel='No stale features with zero code references are being evaluated in the selected environments.'
      nextPage={nextPage}
      prevPage={prevPage}
      goToPage={goToPage}
    />
  )
}

export default MonitorSection
