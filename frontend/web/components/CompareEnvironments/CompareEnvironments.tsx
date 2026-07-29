import React, { FC, useCallback, useEffect, useMemo, useState } from 'react'
import sortBy from 'lodash/sortBy'
import { useHistory } from 'react-router-dom'
import EnvironmentSelect from 'components/EnvironmentSelect'
import Icon from 'components/icons/Icon'
import Panel from 'components/base/grid/Panel'
import Button from 'components/base/forms/Button'
import CreateFlagModal from 'components/modals/create-feature'
import FeatureListStore from 'common/stores/feature-list-store'
import { FeaturesTableFilters } from 'components/pages/features/components'
import Utils from 'common/utils/utils'
import type { FilterState } from 'common/types/featureFilters'
import { SortOrder } from 'common/types/requests'
import {
  getFiltersFromParams,
  hasActiveFilters,
} from 'common/utils/featureFilterParams'
import { matchesProjectFlagFilters } from 'common/utils/filterProjectFlagClientSide'
import CompareFeatureRow, { EditFeatureHandler } from './CompareFeatureRow'
import { ENV_COLUMN_WIDTH, SEGMENTS_COLUMN_WIDTH } from './constants'
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
    // Use shared client-side filter for ProjectFlag properties
    if (
      !matchesProjectFlagFilters(
        item.projectFlagLeft,
        filters,
        filters.tag_strategy,
      )
    ) {
      return false
    }

    // FeatureChange-specific: filter by enabled state in left environment
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

  // The edit modal saves through the legacy Flux store, which RTK Query
  // can't observe — refetch when it reports a change
  useEffect(() => {
    FeatureListStore.on('saved', refresh)
    FeatureListStore.on('removed', refresh)
    return () => {
      FeatureListStore.off('saved', refresh)
      FeatureListStore.off('removed', refresh)
    }
  }, [refresh])

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
      )
    },
    [history, projectIdNum],
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
    // Only show the full loader when there is nothing to display yet;
    // refreshes keep the table visible and dim it instead
    if (isLoading && !changes) {
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
      <div className={isLoading ? 'opacity-50 pe-none' : undefined}>
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
      </div>
    )
  }

  const renderTableHeader = (label: string, count: number) => (
    <Row className='table-header'>
      <div className='table-column flex-fill d-flex align-items-center gap-2'>
        {label}
        <span className='unread px-1'>{count}</span>
      </div>
      <div className='table-column' style={{ width: ENV_COLUMN_WIDTH }}>
        {leftEnvironment?.name}
      </div>
      <div className='table-column' style={{ width: ENV_COLUMN_WIDTH }}>
        {rightEnvironment?.name}
      </div>
      <div
        className='table-column text-end pe-3'
        style={{ width: SEGMENTS_COLUMN_WIDTH }}
      >
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
