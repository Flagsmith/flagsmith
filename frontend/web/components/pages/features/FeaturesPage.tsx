import React, { FC, useCallback, useMemo } from 'react'
import { useHistory } from 'react-router-dom'
import classNames from 'classnames'
import CreateFlagModal from 'components/modals/CreateFlag'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import { config } from 'common/config'
import { useRouteContext } from 'components/providers/RouteContext'
import { usePageTrackingWithContext } from 'common/hooks/usePageTracking'
import PermissionGate from 'components/base/PermissionGate'
import FeatureRow from 'components/feature-summary/FeatureRow'
import JSONReference from 'components/JSONReference'
import Permission from 'common/providers/Permission'
import ErrorMessage from 'components/messages/ErrorMessage'
import {
  FeaturesEmptyState,
  FeatureMetricsSection,
  FeaturesPageHeader,
  FeaturesTableFilters,
  FeaturesSDKIntegration,
} from './components'
import { useFeatureFilters } from './hooks/useFeatureFilters'
import { useRemoveFeatureWithToast } from './hooks/useRemoveFeatureWithToast'
import { useToggleFeatureWithToast } from './hooks/useToggleFeatureWithToast'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import { useFeaturePageDisplay } from './hooks/useFeaturePageDisplay'
import { useFeatureListWithFilters } from 'common/hooks/useFeatureListWithFilters'
import type { Pagination } from './types'
import type { ProjectFlag, FeatureState } from 'common/types/responses'

const DEFAULT_PAGINATION: Pagination = {
  count: 0,
  currentPage: 1,
  next: null,
  pageSize: config.FEATURES_PAGE_SIZE,
  previous: null,
}

const FeaturesPageComponent: FC = () => {
  const history = useHistory()
  const routeContext = useRouteContext()
  const projectId = routeContext.projectId!
  const environmentId = routeContext.environmentId!

  // Project and environment data
  const { getEnvironment, project } = useProjectEnvironments(projectId)

  // Derive page-specific properties
  const maxFeaturesAllowed = project?.max_features_allowed ?? null
  const currentEnvironment = getEnvironment(environmentId)
  const minimumChangeRequestApprovals =
    currentEnvironment?.minimum_change_request_approvals

  // Filters and pagination
  const {
    clearFilters,
    filters,
    goToPage,
    handleFilterChange,
    hasFilters,
    page,
  } = useFeatureFilters(history)

  // Feature actions
  const [removeFeature] = useRemoveFeatureWithToast()
  const [toggleFeature] = useToggleFeatureWithToast()

  const removeFlag = useCallback(
    async (projectFlag: ProjectFlag) => {
      await removeFeature(projectFlag, projectId)
    },
    [removeFeature, projectId],
  )

  const toggleFlag = useCallback(
    async (flag: ProjectFlag, environmentFlag: FeatureState | undefined) => {
      await toggleFeature(flag, environmentFlag, environmentId)
    },
    [toggleFeature, environmentId],
  )

  // Data fetching - API key conversion handled internally
  const { data, error, isFetching, isLoading } = useFeatureListWithFilters(
    filters,
    page,
    environmentId,
    projectId,
  )

  // Extract data with defaults
  const projectFlags = useMemo(() => data?.results ?? [], [data?.results])
  const environmentFlags = useMemo(
    () => data?.environmentStates ?? {},
    [data?.environmentStates],
  )
  const paging = useMemo(
    () => data?.pagination ?? DEFAULT_PAGINATION,
    [data?.pagination],
  )
  const totalFeatures = useMemo(() => data?.count ?? 0, [data?.count])

  // Display state management using custom hook
  const {
    loadedOnce,
    shouldShowCreateButton,
    showContent,
    showEmptyState,
    showInitialLoader,
  } = useFeaturePageDisplay(isLoading, projectFlags, filters, data)

  // Page tracking with environment context
  usePageTrackingWithContext(
    Constants.pages.FEATURES,
    environmentId,
    projectId,
    routeContext.organisationId,
  )

  const newFlag = () => {
    openModal(
      'New Feature',
      <CreateFlagModal
        environmentId={environmentId}
        history={history}
        projectId={projectId}
      />,
      'side-modal create-feature-modal',
    )
  }

  const renderHeader = useCallback(
    () => (
      <FeaturesTableFilters
        projectId={projectId}
        filters={filters}
        hasFilters={hasFilters}
        isLoading={isLoading}
        orgId={routeContext.organisationId}
        onFilterChange={handleFilterChange}
        onClearFilters={clearFilters}
      />
    ),
    [
      projectId,
      filters,
      hasFilters,
      isLoading,
      routeContext.organisationId,
      handleFilterChange,
      clearFilters,
    ],
  )

  const renderFooter = useCallback(
    () => (
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
    ),
    [projectFlags, environmentFlags],
  )

  const renderFeatureRow = useCallback(
    (projectFlag: ProjectFlag, i: number) => (
      <Permission
        level='environment'
        tags={projectFlag.tags}
        permission={Utils.getManageFeaturePermission(
          Utils.changeRequestsEnabled(minimumChangeRequestApprovals),
        )}
        id={environmentId}
      >
        {({ permission }) => (
          <FeatureRow
            environmentFlags={environmentFlags}
            permission={permission}
            environmentId={environmentId}
            projectId={projectId}
            index={i}
            toggleFlag={toggleFlag}
            removeFlag={removeFlag}
            projectFlag={projectFlag}
          />
        )}
      </Permission>
    ),
    [
      environmentFlags,
      environmentId,
      projectId,
      minimumChangeRequestApprovals,
      toggleFlag,
      removeFlag,
    ],
  )

  const handleNextPage = () => {
    if (paging?.next) {
      goToPage(page + 1)
    }
  }

  const handlePrevPage = () => {
    if (paging?.previous) {
      goToPage(page - 1)
    }
  }

  const readOnly = Utils.getFlagsmithHasFeature('read_only_mode')
  return (
    <div
      data-test='features-page'
      id='features-page'
      className='app-container container'
    >
      <div className='features-page'>
        {showInitialLoader && (
          <div className='centered-container'>
            <Loader />
          </div>
        )}

        {(!isLoading || loadedOnce) && (
          <div>
            {showContent ? (
              <div>
                <FeatureMetricsSection
                  environmentId={environmentId}
                  projectId={projectId}
                />

                <FeaturesPageHeader
                  totalFeatures={totalFeatures}
                  maxFeaturesAllowed={maxFeaturesAllowed}
                  showCreateButton={shouldShowCreateButton}
                  onCreateFeature={newFlag}
                  readOnly={readOnly}
                  projectId={projectId}
                />

                <FormGroup
                  className={classNames('mb-4', {
                    'opacity-50': isFetching,
                  })}
                >
                  {error ? (
                    <div className='text-center p-4'>
                      <h4 className='mb-3'>Unable to Load Features</h4>
                      <p className='text-muted mb-3'>
                        We couldn't load your feature flags. This might be due
                        to a network issue or a temporary server problem.
                      </p>
                      <ErrorMessage
                        error={error}
                        errorMessageClass='mb-3 d-inline-flex'
                      />
                      <div>
                        <Button
                          className='btn btn-primary mt-2'
                          onClick={() => window.location.reload()}
                        >
                          Try Again
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <PanelSearch
                      className='no-pad overflow-visible'
                      id='features-list'
                      renderSearchWithNoResults
                      itemHeight={65}
                      isLoading={isLoading}
                      paging={paging}
                      header={renderHeader()}
                      nextPage={handleNextPage}
                      prevPage={handlePrevPage}
                      goToPage={goToPage}
                      items={projectFlags}
                      renderFooter={renderFooter}
                      renderRow={renderFeatureRow}
                    />
                  )}
                </FormGroup>

                <FeaturesSDKIntegration
                  projectId={projectId}
                  environmentId={environmentId}
                />
              </div>
            ) : (
              showEmptyState && (
                <PermissionGate
                  level='project'
                  permission='CREATE_FEATURE'
                  id={projectId}
                >
                  {(perm) => (
                    <FeaturesEmptyState
                      environmentId={environmentId}
                      projectId={projectId}
                      onCreateFeature={newFlag}
                      canCreateFeature={perm}
                    />
                  )}
                </PermissionGate>
              )
            )}
          </div>
        )}
      </div>
    </div>
  )
}

const FeaturesPage = ConfigProvider(FeaturesPageComponent)

export default FeaturesPage
