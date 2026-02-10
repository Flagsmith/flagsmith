import React, { FC, useCallback, useState } from 'react'
import Button from 'components/base/forms/Button'
import SectionShell from './SectionShell'
import { useClientPagination } from 'components/pages/feature-lifecycle/hooks/useClientPagination'
import type { ProjectFlag } from 'common/types/responses'
import type { FilterState } from 'common/types/featureFilters'

type StaleSectionProps = {
  flags: ProjectFlag[]
  isLoading: boolean
  error: unknown
  projectId: number
  filters: FilterState
  hasFilters: boolean
  onFilterChange: (updates: Partial<FilterState>) => void
  onClearFilters: () => void
}

const StaleSection: FC<StaleSectionProps> = ({
  error,
  filters,
  flags,
  hasFilters,
  isLoading,
  onClearFilters,
  onFilterChange,
  projectId,
}) => {
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())

  const { goToPage, nextPage, pageItems, paging, prevPage } =
    useClientPagination({ items: flags })

  const handleSelect = useCallback((flag: ProjectFlag) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(flag.id)) {
        next.delete(flag.id)
      } else {
        next.add(flag.id)
      }
      return next
    })
  }, [])

  const isSelected = useCallback(
    (flag: ProjectFlag) => selectedIds.has(flag.id),
    [selectedIds],
  )

  return (
    <SectionShell
      id='stale-list'
      projectId={projectId}
      items={pageItems}
      paging={paging}
      isLoading={isLoading}
      error={error}
      filters={filters}
      hasFilters={hasFilters}
      onFilterChange={onFilterChange}
      onClearFilters={onClearFilters}
      emptyLabel='No stale features with code references found.'
      nextPage={nextPage}
      prevPage={prevPage}
      goToPage={goToPage}
      isSelected={isSelected}
      onSelect={handleSelect}
      header={
        selectedIds.size > 0 ? (
          <Row className='mb-2 justify-content-end'>
            <Button
              data-test='cleanup-code-btn'
              onClick={() => {
                // TODO: implement code cleanup action
              }}
            >
              {`Cleanup Code (${selectedIds.size})`}
            </Button>
          </Row>
        ) : undefined
      }
    />
  )
}

export default StaleSection
