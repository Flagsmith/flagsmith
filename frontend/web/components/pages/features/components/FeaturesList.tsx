import React, { FC } from 'react'
import { useHistory } from 'react-router-dom'
import classNames from 'classnames'
import FeatureRow from 'components/feature-summary/FeatureRow'
import JSONReference from 'components/JSONReference'
import Permission from 'common/providers/Permission'
import ProjectStore from 'common/stores/project-store'
import { FeaturesTableFilters } from './FeaturesTableFilters'
import type { FilterState } from './FeaturesTableFilters'
import type { FeatureState, ProjectFlag } from 'common/types/responses'

type FeaturesListProps = {
  projectId: string
  environmentId: string
  numericEnvironmentId: number | undefined
  projectFlags: ProjectFlag[]
  environmentFlags: Record<number, FeatureState>
  filters: FilterState
  hasFilters: boolean
  isLoading: boolean
  isFetching: boolean
  paging: any
  page: number
  onFilterChange: (updates: Partial<FilterState>) => void
  onClearFilters: () => void
  onPageChange: (page: number) => void
  onToggleFlag: (flag: any, environmentFlags: any) => Promise<void>
  onRemoveFlag: (projectFlag: any) => Promise<void>
}

export const FeaturesList: FC<FeaturesListProps> = ({
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
  page,
  paging,
  projectFlags,
  projectId,
}) => {
  const history = useHistory()
  const environment = ProjectStore.getEnvironment(environmentId)

  const handleToggleFlag = (
    _projectId: string,
    _environmentId: string,
    flag: any,
    environmentFlags: any,
  ) => {
    return onToggleFlag(flag, environmentFlags)
  }

  const handleRemoveFlag = (_projectId: string, projectFlag: any) => {
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
            orgId={AccountStore.getOrganisation()?.id}
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
