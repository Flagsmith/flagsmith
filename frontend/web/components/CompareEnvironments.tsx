import React, { FC, useCallback, useMemo, useState } from 'react'
import sortBy from 'lodash/sortBy'
import { useHistory } from 'react-router-dom'
import EnvironmentSelect from './EnvironmentSelect'
import data from 'common/data/base/_data'
import ProjectStore from 'common/stores/project-store'
import Icon from './icons/Icon'
import { hasMultivariateChange } from 'common/utils/compareMultivariate'
import Switch from './Switch'
import Panel from './base/grid/Panel'
import Project from 'common/project'
import { FeaturesTableFilters } from './pages/features/components'
import DiffFeature from './diff/DiffFeature'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import FeatureName from './feature-summary/FeatureName'
import FeatureValue from './feature-summary/FeatureValue'
import SegmentsIcon from './icons/SegmentsIcon'
import Button from './base/forms/Button'
import CreateFlagModal from './modals/create-feature'
import Utils from 'common/utils/utils'
import {
  Environment,
  FeatureState,
  FeatureStateWithConflict,
  ProjectFlag,
  TagStrategy,
} from 'common/types/responses'
import type { FilterState } from 'common/types/featureFilters'
import { SortOrder } from 'common/types/requests'
import {
  hasActiveFilters,
  getFiltersFromParams,
} from 'common/utils/featureFilterParams'

type FeatureChange = {
  leftEnabled: boolean
  leftValue: string | number | boolean | null
  leftEnvironmentFlag: FeatureState
  rightEnabled: boolean
  rightValue: string | number | boolean | null
  rightEnvironmentFlag: FeatureState
  projectFlagLeft: ProjectFlag
  projectFlagRight: ProjectFlag
  enabledChanged: boolean
  valueChanged: boolean
  multivariateChanged: boolean
  hasDiff: boolean
}

type CompareEnvironmentsProps = {
  projectId: string
  environmentId?: string
}

type ExpandedRowProps = {
  item: FeatureChange
  projectId: string
  environmentLeftId: number
  environmentRightId: number
  oldEnvName?: string
  newEnvName?: string
}

const ExpandedRow: FC<ExpandedRowProps> = ({
  environmentLeftId,
  environmentRightId,
  item,
  newEnvName,
  oldEnvName,
  projectId,
}) => {
  const { data: leftStates, isLoading: leftLoading } = useGetFeatureStatesQuery(
    {
      environment: environmentLeftId,
      feature: item.projectFlagLeft.id,
    },
  )

  const { data: rightStates, isLoading: rightLoading } =
    useGetFeatureStatesQuery({
      environment: environmentRightId,
      feature: item.projectFlagLeft.id,
    })

  if (leftLoading || rightLoading) {
    return (
      <div className='p-4 text-center'>
        <Loader />
      </div>
    )
  }

  return (
    <div className='px-4 py-3 bg-light200'>
      <DiffFeature
        featureId={item.projectFlagLeft.id}
        projectId={projectId}
        environmentId={String(environmentRightId)}
        oldState={
          (leftStates?.results || []) as unknown as FeatureStateWithConflict[]
        }
        newState={
          (rightStates?.results || []) as unknown as FeatureStateWithConflict[]
        }
        oldEnvName={oldEnvName}
        newEnvName={newEnvName}
        noChangesMessage='No differences between environments'
        tabTheme='pill'
      />
    </div>
  )
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
  const [isLoading, setIsLoading] = useState(false)
  const [changes, setChanges] = useState<FeatureChange[] | null>(null)
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set())
  const [filters, setFilters] = useState<FilterState>(getFiltersFromParams({}))

  const projectIdNum = parseInt(projectId)

  const editFeature = (
    projectFlag: ProjectFlag,
    environmentFlag: FeatureState,
    environmentId: string,
    environmentName?: string,
  ) => {
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
        environmentId={environmentId}
        projectFlag={projectFlag}
        projectId={projectId}
        history={history}
      />,
      'side-modal create-feature-modal',
      () => {
        fetch()
      },
    )
  }

  const fetch = useCallback(async () => {
    if (!environmentLeft || !environmentRight) {
      return
    }
    setIsLoading(true)
    try {
      const [
        environmentLeftProjectFlags,
        environmentRightProjectFlags,
        environmentLeftFlags,
        environmentRightFlags,
      ] = await Promise.all([
        data.get(
          `${
            Project.api
          }projects/${projectId}/features/?page_size=999&environment=${ProjectStore.getEnvironmentIdFromKey(
            environmentLeft,
          )}`,
        ),
        data.get(
          `${
            Project.api
          }projects/${projectId}/features/?page_size=999&environment=${ProjectStore.getEnvironmentIdFromKey(
            environmentRight,
          )}`,
        ),
        data.get(
          `${Project.api}environments/${environmentLeft}/featurestates/?page_size=999`,
        ),
        data.get(
          `${Project.api}environments/${environmentRight}/featurestates/?page_size=999`,
        ),
      ])

      const changesArr: FeatureChange[] = []

      sortBy(environmentLeftProjectFlags.results, (p) => p.name).forEach(
        (projectFlagLeft: ProjectFlag) => {
          const projectFlagRight = environmentRightProjectFlags.results?.find(
            (pf: ProjectFlag) => pf.id === projectFlagLeft.id,
          )
          const leftSide = environmentLeftFlags.results.find(
            (v: FeatureState) => v.feature === projectFlagLeft.id,
          )
          const rightSide = environmentRightFlags.results.find(
            (v: FeatureState) => v.feature === projectFlagLeft.id,
          )

          if (!leftSide || !rightSide) return

          const enabledChanged = rightSide.enabled !== leftSide.enabled
          const valueChanged =
            rightSide.feature_state_value !== leftSide.feature_state_value
          const multivariateChanged = hasMultivariateChange(leftSide, rightSide)

          const hasDiff =
            enabledChanged ||
            valueChanged ||
            multivariateChanged ||
            !!projectFlagLeft.num_segment_overrides ||
            !!projectFlagRight?.num_segment_overrides

          const change: FeatureChange = {
            enabledChanged,
            hasDiff,
            leftEnabled: leftSide.enabled,
            leftEnvironmentFlag: leftSide,
            leftValue: leftSide.feature_state_value,
            multivariateChanged,
            projectFlagLeft,
            projectFlagRight,
            rightEnabled: rightSide.enabled,
            rightEnvironmentFlag: rightSide,
            rightValue: rightSide.feature_state_value,
            valueChanged,
          }

          changesArr.push(change)
        },
      )

      setChanges(changesArr)
      setExpandedRows(new Set())
    } catch {
      // Error handling
    } finally {
      setIsLoading(false)
    }
  }, [environmentLeft, environmentRight, projectId])

  React.useEffect(() => {
    fetch()
  }, [fetch])

  const filterItems = useCallback(
    (items: FeatureChange[] | null): FeatureChange[] => {
      if (!items) return []

      let filtered = items.filter((item) => {
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
              } else {
                if (!tagIds.some((tagId) => featureTags.includes(tagId))) {
                  return false
                }
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
          const groupIds =
            item.projectFlagLeft.group_owners?.map((g) => g.id) || []
          if (!filters.group_owners.some((id) => groupIds.includes(id))) {
            return false
          }
        }

        if (filters.is_enabled !== null) {
          if (item.leftEnabled !== filters.is_enabled) {
            return false
          }
        }

        return true
      })

      if (filters.sort.sortBy === 'created_date') {
        filtered = sortBy(filtered, (f) => f.projectFlagLeft.created_date)
        if (filters.sort.sortOrder === SortOrder.DESC) {
          filtered = filtered.reverse()
        }
      } else {
        filtered = sortBy(filtered, (f) => f.projectFlagLeft.name.toLowerCase())
        if (filters.sort.sortOrder === SortOrder.DESC) {
          filtered = filtered.reverse()
        }
      }

      return filtered
    },
    [filters],
  )

  const filteredItems = useMemo(
    () => filterItems(changes),
    [changes, filterItems],
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

  const envLeft = ProjectStore.getEnvironment(environmentLeft) as
    | Environment
    | undefined
    | null
  const envRight = ProjectStore.getEnvironment(environmentRight) as
    | Environment
    | undefined
    | null

  const envLeftId = ProjectStore.getEnvironmentIdFromKey(environmentLeft)
  const envRightId = ProjectStore.getEnvironmentIdFromKey(environmentRight)

  const hasFilters = hasActiveFilters(filters)

  const renderRow = (item: FeatureChange, index: number) => {
    const isExpanded = expandedRows.has(item.projectFlagLeft.id)
    const totalSegments = Math.max(
      item.projectFlagLeft.num_segment_overrides || 0,
      item.projectFlagRight?.num_segment_overrides || 0,
    )

    return (
      <div key={item.projectFlagLeft.id} className='list-item list-item-xs'>
        <div
          className='clickable d-flex align-items-center py-2'
          data-test={`compare-item-${index}`}
          onClick={() => toggleExpand(item.projectFlagLeft.id)}
        >
          <div className='table-column flex-row flex-fill align-items-center'>
            <Icon
              name={isExpanded ? 'chevron-down' : 'chevron-right'}
              width={16}
              className='me-2'
            />
            <FeatureName name={item.projectFlagLeft.name} />
          </div>

          <div
            className='table-column d-flex align-items-center gap-2'
            style={{ width: 280 }}
          >
            <Switch checked={item.leftEnabled} disabled />
            <FeatureValue value={item.leftValue} />
            <div className='flex-fill' />
            <Button
              theme='text'
              size='xSmall'
              onClick={(e: React.MouseEvent) => {
                e.stopPropagation()
                editFeature(
                  item.projectFlagLeft,
                  item.leftEnvironmentFlag,
                  environmentLeft,
                  envLeft?.name,
                )
              }}
            >
              Edit
            </Button>
          </div>

          <div
            className='table-column d-flex align-items-center gap-2'
            style={{ width: 280 }}
          >
            <Switch checked={item.rightEnabled} disabled />
            <FeatureValue value={item.rightValue} />
            <div className='flex-fill' />
            <Button
              theme='text'
              size='xSmall'
              onClick={(e: React.MouseEvent) => {
                e.stopPropagation()
                editFeature(
                  item.projectFlagRight,
                  item.rightEnvironmentFlag,
                  environmentRight,
                  envRight?.name,
                )
              }}
            >
              Edit
            </Button>
          </div>

          <div
            className='table-column d-flex justify-content-end pe-3'
            style={{ width: 140 }}
          >
            {totalSegments > 0 && (
              <span className='chip chip--xs bg-primary text-white d-inline-flex align-items-center gap-1'>
                <SegmentsIcon className='chip-svg-icon' />
                {totalSegments}
              </span>
            )}
          </div>
        </div>

        {isExpanded && envLeftId && envRightId && (
          <ExpandedRow
            item={item}
            projectId={projectId}
            environmentLeftId={envLeftId}
            environmentRightId={envRightId}
            oldEnvName={envLeft?.name}
            newEnvName={envRight?.name}
          />
        )}
      </div>
    )
  }

  const renderHeader = () => (
    <FeaturesTableFilters
      projectId={projectIdNum}
      filters={filters}
      hasFilters={hasFilters}
      isLoading={isLoading}
      onFilterChange={handleFilterChange}
      onClearFilters={clearFilters}
    />
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

      {environmentLeft && environmentRight && (
        <>
          {isLoading ? (
            <div className='text-center py-4'>
              <Loader />
            </div>
          ) : (
            <>
              <Panel className='no-pad mb-4'>
                <div className='search-list'>
                  {renderHeader()}
                  <Row className='table-header'>
                    <div className='table-column flex-fill d-flex align-items-center gap-2'>
                      Changed features
                      <span className='unread px-1'>
                        {differentItems.length}
                      </span>
                    </div>
                    <div className='table-column' style={{ width: 280 }}>
                      {envLeft?.name}
                    </div>
                    <div className='table-column' style={{ width: 280 }}>
                      {envRight?.name}
                    </div>
                    <div
                      className='table-column text-end pe-3'
                      style={{ width: 140 }}
                    >
                      Segment changes
                    </div>
                  </Row>
                  {differentItems.length > 0 &&
                    differentItems.map((item, i) => renderRow(item, i))}
                  {!differentItems.length && (
                    <div className='text-center py-3 text-muted fs-small'>
                      No differences found
                    </div>
                  )}
                </div>
              </Panel>

              {sameItems.length > 0 && (
                <Panel className='no-pad'>
                  <div className='search-list'>
                    <Row className='table-header'>
                      <div className='table-column flex-fill d-flex align-items-center gap-2'>
                        Unchanged features
                        <span className='unread px-1'>{sameItems.length}</span>
                      </div>
                      <div className='table-column' style={{ width: 280 }}>
                        {envLeft?.name}
                      </div>
                      <div className='table-column' style={{ width: 280 }}>
                        {envRight?.name}
                      </div>
                      <div
                        className='table-column text-end pe-3'
                        style={{ width: 140 }}
                      >
                        Segment changes
                      </div>
                    </Row>
                    {sameItems.map((item, i) => renderRow(item, i))}
                  </div>
                </Panel>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}

export default CompareEnvironments
