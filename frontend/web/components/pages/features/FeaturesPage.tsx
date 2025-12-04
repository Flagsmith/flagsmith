import React, { FC } from 'react'
import { useHistory } from 'react-router-dom'
import CreateFlagModal from 'components/modals/CreateFlag'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import { config } from 'common/config'
import { useRouteContext } from 'components/providers/RouteContext'
import { usePageTrackingWithContext } from 'common/hooks/usePageTracking'
import PermissionGate from 'components/base/PermissionGate'
import {
  FeaturesEmptyState,
  FeatureMetricsSection,
  FeaturesPageHeader,
  FeaturesList,
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

  const removeFlag = async (projectFlag: ProjectFlag) => {
    await removeFeature(projectFlag, projectId)
  }

  const toggleFlag = async (
    flag: ProjectFlag,
    environmentFlag: FeatureState | undefined,
  ) => {
    await toggleFeature(flag, environmentFlag, environmentId)
  }

  // Data fetching - API key conversion handled internally
  const { data, isFetching, isLoading } = useFeatureListWithFilters(
    filters,
    page,
    environmentId,
    projectId,
  )

  // Extract data with defaults
  const projectFlags = data?.results ?? []
  const environmentFlags = data?.environmentStates ?? {}
  const paging = data?.pagination ?? DEFAULT_PAGINATION
  const totalFeatures = data?.count ?? 0

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

                <FeaturesList
                  projectId={projectId}
                  environmentId={environmentId}
                  minimumChangeRequestApprovals={minimumChangeRequestApprovals}
                  organisationId={routeContext.organisationId}
                  projectFlags={projectFlags}
                  environmentFlags={environmentFlags}
                  filters={filters}
                  hasFilters={hasFilters}
                  isLoading={isLoading}
                  isFetching={isFetching}
                  paging={paging}
                  page={page}
                  onFilterChange={handleFilterChange}
                  onClearFilters={clearFilters}
                  onPageChange={goToPage}
                  onToggleFlag={toggleFlag}
                  onRemoveFlag={removeFlag}
                />

                <FeaturesSDKIntegration
                  projectId={projectId}
                  environmentId={environmentId}
                  firstFeatureName={projectFlags?.[0]?.name}
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
