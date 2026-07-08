import React, { FC, useCallback, useEffect, useMemo, useState } from 'react'
import sortBy from 'lodash/sortBy'
import { useHistory } from 'react-router-dom'
import EnvironmentSelect from 'components/EnvironmentSelect'
import Icon from 'components/icons/Icon'
import Panel from 'components/base/grid/Panel'
import Button from 'components/base/forms/Button'
import CreateFlagModal from 'components/modals/create-feature'
import { FeaturesTableFilters } from 'components/pages/features/components'
import Utils from 'common/utils/utils'
import { TagStrategy } from 'common/types/responses'
import type { FilterState } from 'common/types/featureFilters'
import { SortOrder } from 'common/types/requests'
import {
  getFiltersFromParams,
  hasActiveFilters,
} from 'common/utils/featureFilterParams'
import CompareFeatureRow, { EditFeatureHandler } from './CompareFeatureRow'
import { FeatureChange } from './types'
import { useEnvironmentComparison } from './useEnvironmentComparison'

type CompareEnvironmentsProps = {
  projectId: string
  environmentId?: string
}

const filterAndSortChanges = (
  items: FeatureChange[] | null,
  filters: FilterState,
): FeatureChange[] => {
  if (!items) return []

  const filtered = items.filter((item) => {
    if (!filters.showArchived && item.projectFlagLeft.is_archived) {
      return false
    }

    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      if (!item.projectFlagLeft.name.toLowerCase().includes(searchLower)) {
        return false
      }
    }

    if (filters.tags.length > 0) {
      const featureTags = item.projectFlagLeft.tags || []

      if (filters.tags.includes('')) {
        if (featureTags.length > 0) {
          return false
        }
      } else {
        const tagIds = filters.tags.filter((t) => t !== '') as number[]
        if (tagIds.length > 0) {
          if (filters.tag_strategy === TagStrategy.INTERSECTION) {
            if (!tagIds.every((tagId) => featureTags.includes(tagId))) {
              return false
            }
          } else if (!tagIds.some((tagId) => featureTags.includes(tagId))) {
            return false
          }
        }
      }
    }

    if (filters.owners.length > 0) {
      const ownerIds = item.projectFlagLeft.owners?.map((o) => o.id) || []
      if (!filters.owners.some((id) => ownerIds.includes(id))) {
        return false
      }
    }

    if (filters.group_owners.length > 0) {
      const groupIds = item.projectFlagLeft.group_owners?.map((g) => g.id) || []
      if (!filters.group_owners.some((id) => groupIds.includes(id))) {
        return false
      }
    }

    if (
      filters.is_enabled !== null &&
      item.leftEnabled !== filters.is_enabled
    ) {
      return false
    }

    return true
  })

  const sorted =
    filters.sort.sortBy === 'created_date'
      ? sortBy(filtered, (f) => f.projectFlagLeft.created_date)
      : sortBy(filtered, (f) => f.projectFlagLeft.name.toLowerCase())

  return filters.sort.sortOrder === SortOrder.DESC ? sorted.reverse() : sorted
}

const CompareEnvironments: FC<CompareEnvironmentsProps> = ({
  environmentId: initialEnvironmentId,
  projectId,
}) => {
  const history = useHistory()
  const [environmentLeft, setEnvironmentLeft] = useState<string>(
    initialEnvironmentId || '',
  )
  const [environmentRight, setEnvironmentRight] = useState<string>('')
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set())
  const [filters, setFilters] = useState<FilterState>(getFiltersFromParams({}))

  const projectIdNum = parseInt(projectId)

  const {
    changes,
    error,
    isLoading,
    leftEnvironment,
    leftEnvironmentId,
    refresh,
    rightEnvironment,
    rightEnvironmentId,
  } = useEnvironmentComparison({
    leftEnvironmentKey: environmentLeft,
    projectId,
    rightEnvironmentKey: environmentRight,
  })

  // Collapse any expanded rows whenever a fresh comparison loads
  useEffect(() => {
    setExpandedRows(new Set())
  }, [changes])

  const editFeature: EditFeatureHandler = useCallback(
    (projectFlag, environmentFlag, environmentKey, environmentName) => {
      openModal(
        <Row className='align-items-center'>
          <span>
            Edit Feature: {projectFlag.name}
            {environmentName && (
              <span className='text-muted ms-2'>({environmentName})</span>
            )}
          </span>
          <Button
            onClick={() => {
              Utils.copyToClipboard(projectFlag.name)
            }}
            theme='icon'
            className='ms-2'
          >
            <Icon name='copy' />
          </Button>
        </Row>,
        <CreateFlagModal
          environmentFlag={environmentFlag}
          environmentId={environmentKey}
          projectFlag={projectFlag}
          projectId={projectIdNum}
          history={history}
        />,
        'side-modal create-feature-modal',
        () => {
          refresh()
        },
      )
    },
    [history, projectIdNum, refresh],
  )

  const filteredItems = useMemo(
    () => filterAndSortChanges(changes, filters),
    [changes, filters],
  )

  const differentItems = useMemo(
    () => filteredItems.filter((item) => item.hasDiff),
    [filteredItems],
  )

  const sameItems = useMemo(
    () => filteredItems.filter((item) => !item.hasDiff),
    [filteredItems],
  )

  const toggleExpand = (featureId: number) => {
    setExpandedRows((prev) => {
      const next = new Set(prev)
      if (next.has(featureId)) {
        next.delete(featureId)
      } else {
        next.add(featureId)
      }
      return next
    })
  }

  const handleFilterChange = (updates: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...updates }))
  }

  const clearFilters = () => {
    setFilters(getFiltersFromParams({}))
  }

  const hasFilters = hasActiveFilters(filters)

  const renderRow = (item: FeatureChange, index: number) => (
    <CompareFeatureRow
      key={item.projectFlagLeft.id}
      item={item}
      index={index}
      projectId={projectId}
      isExpanded={expandedRows.has(item.projectFlagLeft.id)}
      onToggle={toggleExpand}
      onEdit={editFeature}
      leftEnvironmentKey={environmentLeft}
      rightEnvironmentKey={environmentRight}
      leftEnvironmentId={leftEnvironmentId}
      rightEnvironmentId={rightEnvironmentId}
      leftEnvironmentName={leftEnvironment?.name}
      rightEnvironmentName={rightEnvironment?.name}
    />
  )

  const renderResults = () => {
    if (isLoading) {
      return (
        <div className='text-center py-4'>
          <Loader />
        </div>
      )
    }

    if (error) {
      return (
        <div className='text-center py-4 text-muted'>
          Could not load the comparison.{' '}
          <Button theme='text' onClick={() => refresh()}>
            Try again
          </Button>
        </div>
      )
    }

    return (
      <>
        <Panel className='no-pad mb-4'>
          <div className='search-list'>
            <FeaturesTableFilters
              projectId={projectIdNum}
              filters={filters}
              hasFilters={hasFilters}
              isLoading={isLoading}
              onFilterChange={handleFilterChange}
              onClearFilters={clearFilters}
            />
            {renderTableHeader('Changed features', differentItems.length)}
            {differentItems.length > 0 ? (
              differentItems.map((item, i) => renderRow(item, i))
            ) : (
              <div className='text-center py-3 text-muted fs-small'>
                No differences found
              </div>
            )}
          </div>
        </Panel>

        {sameItems.length > 0 && (
          <Panel className='no-pad'>
            <div className='search-list'>
              {renderTableHeader('Unchanged features', sameItems.length)}
              {sameItems.map((item, i) => renderRow(item, i))}
            </div>
          </Panel>
        )}
      </>
    )
  }

  const renderTableHeader = (label: string, count: number) => (
    <Row className='table-header'>
      <div className='table-column flex-fill d-flex align-items-center gap-2'>
        {label}
        <span className='unread px-1'>{count}</span>
      </div>
      <div className='table-column' style={{ width: 280 }}>
        {leftEnvironment?.name}
      </div>
      <div className='table-column' style={{ width: 280 }}>
        {rightEnvironment?.name}
      </div>
      <div className='table-column text-end pe-3' style={{ width: 140 }}>
        Segment changes
      </div>
    </Row>
  )

  return (
    <div>
      <div className='col-md-8'>
        <h5 className='mb-1'>Compare Environments</h5>
        <p className='fs-small mb-4 lh-sm'>
          Compare feature flag configurations across environments.
        </p>
      </div>

      <Row className='mb-4'>
        <div style={{ width: 300 }}>
          <EnvironmentSelect
            ignore={environmentRight ? [environmentRight] : undefined}
            projectId={projectIdNum}
            onChange={(value) => setEnvironmentLeft(value as string)}
            value={environmentLeft}
          />
        </div>

        <div className='mx-3 d-flex align-items-center'>
          <Icon name='arrow-right' width={20} />
        </div>

        <div style={{ width: 300 }}>
          <EnvironmentSelect
            projectId={projectIdNum}
            ignore={environmentLeft ? [environmentLeft] : undefined}
            onChange={(value) => setEnvironmentRight(value as string)}
            value={environmentRight}
          />
        </div>
      </Row>

      {environmentLeft && environmentRight && renderResults()}
    </div>
  )
}

export default CompareEnvironments
