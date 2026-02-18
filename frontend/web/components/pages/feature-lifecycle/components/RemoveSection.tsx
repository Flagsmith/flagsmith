import React, { FC, useCallback, useState } from 'react'
import Button from 'components/base/forms/Button'
import SectionShell from './SectionShell'
import { useClientPagination } from 'components/pages/feature-lifecycle/hooks/useClientPagination'
import type { ProjectFlag } from 'common/types/responses'
import type { FilterState } from 'common/types/featureFilters'

type RemoveSectionProps = {
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

const RemoveSection: FC<RemoveSectionProps> = ({
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
      id='remove-list'
      projectId={projectId}
      items={pageItems}
      paging={paging}
      isLoading={isLoading}
      error={error}
      filters={filters}
      hasFilters={hasFilters}
      onFilterChange={onFilterChange}
      onClearFilters={onClearFilters}
      emptyLabel='No stale features found with zero code references and zero evaluations in the selected environments and period.'
      nextPage={nextPage}
      prevPage={prevPage}
      goToPage={goToPage}
      isSelected={isSelected}
      onSelect={handleSelect}
      header={
        selectedIds.size > 0 ? (
          <Row className='mb-2 justify-content-end'>
            <Button
              data-test='remove-flags-btn'
              onClick={() => {
                // TODO: implement bulk flag removal
              }}
            >
              {`Remove Flags (${selectedIds.size})`}
            </Button>
          </Row>
        ) : undefined
      }
    />
  )
}

export default RemoveSection
