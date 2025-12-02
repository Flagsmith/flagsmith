import React, { FC } from 'react'
import { useHistory } from 'react-router-dom'
import classNames from 'classnames'
import FeatureRow from 'components/feature-summary/FeatureRow'
import JSONReference from 'components/JSONReference'
import Permission from 'common/providers/Permission'
import { FeaturesTableFilters } from './FeaturesTableFilters'
import type { FilterState } from './FeaturesTableFilters'
import type {
  Environment,
  FeatureState,
  ProjectFlag,
} from 'common/types/responses'
import type { Pagination } from 'components/pages/features/types'

type FeaturesListProps = {
  projectId: string
  environmentId: string
  numericEnvironmentId: number | undefined
  environment: Environment | undefined
  organisationId: number | undefined
  projectFlags: ProjectFlag[]
  environmentFlags: Record<number, FeatureState>
  filters: FilterState
  hasFilters: boolean
  isLoading: boolean
  isFetching: boolean
  paging: Pagination
  page: number
  onFilterChange: (updates: Partial<FilterState>) => void
  onClearFilters: () => void
  onPageChange: (page: number) => void
  onToggleFlag: (
    flag: ProjectFlag,
    environmentFlags: Record<number, FeatureState>,
  ) => Promise<void>
  onRemoveFlag: (projectFlag: ProjectFlag) => Promise<void>
}

export const FeaturesList: FC<FeaturesListProps> = ({
  environment,
  environmentFlags,
  environmentId,
  filters,
  hasFilters,
  isFetching,
  isLoading,
  numericEnvironmentId,
  onClearFilters,
  onFilterChange,
  onPageChange,
  onRemoveFlag,
  onToggleFlag,
  organisationId,
  page,
  paging,
  projectFlags,
  projectId,
}) => {
  const history = useHistory()

  const handleToggleFlag = (
    _projectId: string,
    _environmentId: string,
    flag: ProjectFlag,
    environmentFlags: Record<number, FeatureState>,
  ) => {
    return onToggleFlag(flag, environmentFlags)
  }

  const handleRemoveFlag = (_projectId: string, projectFlag: ProjectFlag) => {
    return onRemoveFlag(projectFlag)
  }

  return (
    <FormGroup
      className={classNames('mb-4', {
        'opacity-50': isFetching,
      })}
    >
      <PanelSearch
        className='no-pad overflow-visible'
        id='features-list'
        renderSearchWithNoResults
        itemHeight={65}
        isLoading={isLoading}
        paging={paging}
        header={
          <FeaturesTableFilters
            projectId={projectId}
            environmentId={numericEnvironmentId?.toString() || ''}
            filters={filters}
            hasFilters={hasFilters}
            isLoading={isLoading}
            orgId={organisationId}
            onFilterChange={onFilterChange}
            onClearFilters={onClearFilters}
          />
        }
        nextPage={() => paging?.next && onPageChange(page + 1)}
        prevPage={() => paging?.previous && onPageChange(page - 1)}
        goToPage={onPageChange}
        items={projectFlags?.filter((v) => !v.ignore)}
        renderFooter={() => (
          <>
            <JSONReference
              className='mx-2 mt-4'
              showNamesButton
              title={'Features'}
              json={projectFlags}
            />
            <JSONReference
              className='mx-2'
              title={'Feature States'}
              json={environmentFlags && Object.values(environmentFlags)}
            />
          </>
        )}
        renderRow={(projectFlag, i) => (
          <Permission
            level='environment'
            tags={projectFlag.tags}
            permission={Utils.getManageFeaturePermission(
              Utils.changeRequestsEnabled(
                environment && environment.minimum_change_request_approvals,
              ),
            )}
            id={environmentId}
          >
            {({ permission }) => (
              <FeatureRow
                environmentFlags={environmentFlags}
                permission={permission}
                history={history}
                environmentId={environmentId}
                projectId={projectId}
                index={i}
                canDelete={permission}
                toggleFlag={handleToggleFlag}
                removeFlag={handleRemoveFlag}
                projectFlag={projectFlag}
              />
            )}
          </Permission>
        )}
      />
    </FormGroup>
  )
}
