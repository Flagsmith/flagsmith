import React, { FC } from 'react'
import SectionShell from './SectionShell'
import { useClientPagination } from 'components/pages/feature-lifecycle/hooks/useClientPagination'
import type { ProjectFlag } from 'common/types/responses'
import type { FilterState } from 'common/types/featureFilters'

type PermanentSectionProps = {
  flags: ProjectFlag[]
  isLoading: boolean
  error: unknown
  projectId: number
  filters: FilterState
  hasFilters: boolean
  onFilterChange: (updates: Partial<FilterState>) => void
  onClearFilters: () => void
}

const PermanentSection: FC<PermanentSectionProps> = ({
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
      id='permanent-list'
      projectId={projectId}
      items={pageItems}
      paging={paging}
      isLoading={isLoading}
      error={error}
      filters={filters}
      hasFilters={hasFilters}
      onFilterChange={onFilterChange}
      onClearFilters={onClearFilters}
      emptyLabel='No permanent features found.'
      nextPage={nextPage}
      prevPage={prevPage}
      goToPage={goToPage}
    />
  )
}

export default PermanentSection
