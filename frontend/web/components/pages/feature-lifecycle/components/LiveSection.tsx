import React, { FC } from 'react'
import SectionShell from './SectionShell'
import { useClientPagination } from 'components/pages/feature-lifecycle/hooks/useClientPagination'
import type { ProjectFlag } from 'common/types/responses'
import type { FilterState } from 'common/types/featureFilters'

type LiveSectionProps = {
  flags: ProjectFlag[]
  isLoading: boolean
  error: unknown
  projectId: number
  filters: FilterState
  hasFilters: boolean
  onFilterChange: (updates: Partial<FilterState>) => void
  onClearFilters: () => void
}

const LiveSection: FC<LiveSectionProps> = ({
  error,
  filters,
  flags,
  hasFilters,
  isLoading,
  onClearFilters,
  onFilterChange,
  projectId,
}) => {
  const { goToPage, nextPage, pageItems, paging, prevPage } =
    useClientPagination({ items: flags })

  return (
    <SectionShell
      id='live-list'
      projectId={projectId}
      items={pageItems}
      paging={paging}
      isLoading={isLoading}
      error={error}
      filters={filters}
      hasFilters={hasFilters}
      onFilterChange={onFilterChange}
      onClearFilters={onClearFilters}
      emptyLabel='No live flags with code references found.'
      nextPage={nextPage}
      prevPage={prevPage}
      goToPage={goToPage}
    />
  )
}

export default LiveSection
