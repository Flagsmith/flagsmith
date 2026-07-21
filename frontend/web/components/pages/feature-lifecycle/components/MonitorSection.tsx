import React, { FC } from 'react'
import SectionShell from './SectionShell'
import { useClientPagination } from 'components/pages/feature-lifecycle/hooks/useClientPagination'
import type { ProjectFlag } from 'common/types/responses'
import type { FilterState } from 'common/types/featureFilters'

type MonitorSectionProps = {
  flags: ProjectFlag[]
  isLoading: boolean
  error: unknown
  projectId: number
  filters: FilterState
  hasFilters: boolean
  onFilterChange: (updates: Partial<FilterState>) => void
  onClearFilters: () => void
  onFeatureClick?: (flag: ProjectFlag) => void
}

const MonitorSection: FC<MonitorSectionProps> = ({
  error,
  filters,
  flags,
  hasFilters,
  isLoading,
  onClearFilters,
  onFeatureClick,
  onFilterChange,
  projectId,
}) => {
  const { goToPage, nextPage, pageItems, paging, prevPage } =
    useClientPagination({ items: flags })

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
      onFeatureClick={onFeatureClick}
      emptyLabel='No stale features with zero code references are being evaluated in this environment.'
      nextPage={nextPage}
      prevPage={prevPage}
      goToPage={goToPage}
    />
  )
}

export default MonitorSection
