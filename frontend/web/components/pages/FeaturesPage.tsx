import React, { FC, useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, useHistory } from 'react-router-dom'
import CreateFlagModal from 'components/modals/CreateFlag'
import Permission from 'common/providers/Permission'
import ConfigProvider from 'common/providers/ConfigProvider'
import { config } from 'common/config'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import { useRouteContext } from 'components/providers/RouteContext'
import {
  FeaturesEmptyState,
  FeatureMetricsSection,
  FeaturesPageHeader,
  FeaturesList,
  FeaturesSDKIntegration,
} from './features'
import {
  shouldShowInitialLoader,
  shouldShowContent,
  shouldShowEmptyState,
} from './features/utils/displayLogic'
import { buildApiFilterParams } from './features/utils/filterHelpers'
import { useGetFeatureListQuery } from 'common/services/useFeatureList'
import { useFeatureFilters } from './features/hooks/useFeatureFilters'
import { useFeatureActions } from './features/hooks/useFeatureActions'
import { useProjectEnvironments } from './features/hooks/useProjectEnvironments'

type RouteParams = {
  environmentId: string
  projectId: string
}

const FeaturesPageComponent: FC = () => {
  const { environmentId, projectId: projectIdParam } = useParams<RouteParams>()
  const history = useHistory()
  const routeContext = useRouteContext()
  const projectId = routeContext.projectId ?? parseInt(projectIdParam)

  const {
    getEnvironment,
    getEnvironmentIdFromKey,
    isLoading: isLoadingEnvironments,
    maxFeaturesAllowed,
  } = useProjectEnvironments(projectId)

  const numericEnvironmentId = useMemo(
    () => getEnvironmentIdFromKey(environmentId),
    [getEnvironmentIdFromKey, environmentId],
  )

  const environment = useMemo(
    () => getEnvironment(environmentId),
    [getEnvironment, environmentId],
  )

  const {
    clearFilters,
    filters,
    goToPage,
    handleFilterChange,
    hasFilters,
    page,
  } = useFeatureFilters(history)

  const { removeFlag, toggleFlag } = useFeatureActions(projectId, environmentId)

  const [loadedOnce, setLoadedOnce] = useState(false)

  const { data, isFetching, isLoading } = useGetFeatureListQuery(
    buildApiFilterParams(
      filters,
      page,
      numericEnvironmentId?.toString() ?? '',
      projectId,
    ),
    {
      skip: !numericEnvironmentId || !projectId || isLoadingEnvironments,
    },
  )

  const projectFlags = data?.results ?? []
  const environmentFlags = data?.environmentStates ?? {}
  const paging = data?.pagination ?? {
    count: 0,
    currentPage: 1,
    next: null,
    pageSize: config.FEATURES_PAGE_SIZE,
    previous: null,
  }
  const totalFeatures = data?.count ?? 0

  useEffect(() => {
    API.trackPage(Constants.pages.FEATURES)
    AsyncStorage.setItem(
      'lastEnv',
      JSON.stringify({
        environmentId,
        orgId: routeContext.organisationId,
        projectId,
      }),
    )
  }, [environmentId, projectId, routeContext.organisationId])

  useEffect(() => {
    if (data && !loadedOnce) {
      setLoadedOnce(true)
    }
  }, [data, loadedOnce])

  const newFlag = useCallback((): void => {
    openModal(
      'New Feature',
      <CreateFlagModal
        history={history}
        environmentId={environmentId}
        projectId={projectId}
      />,
      'side-modal create-feature-modal',
    )
  }, [history, environmentId, projectId])

  const createFeaturePermission = useCallback(
    (el: (permission: boolean) => React.ReactNode): React.ReactNode => {
      return (
        <Permission level='project' permission='CREATE_FEATURE' id={projectId}>
          {({ permission }) =>
            permission
              ? el(permission)
              : Utils.renderWithPermission(
                  permission,
                  Constants.projectPermissions('Create Feature'),
                  el(permission),
                )
          }
        </Permission>
      )
    },
    [projectId],
  )

  const readOnly = Utils.getFlagsmithHasFeature('read_only_mode')

  const showInitialLoader = shouldShowInitialLoader(
    isLoading,
    loadedOnce,
    projectFlags,
  )
  const showContent = shouldShowContent(loadedOnce, filters, isLoading)
  const showEmptyState = shouldShowEmptyState(
    isLoading,
    loadedOnce,
    showContent,
  )

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
                  environmentApiKey={environment?.api_key}
                  projectId={projectId}
                />

                <FeaturesPageHeader
                  totalFeatures={totalFeatures}
                  maxFeaturesAllowed={maxFeaturesAllowed}
                  showCreateButton={
                    loadedOnce || filters.showArchived || !!filters.tags?.length
                  }
                  onCreateFeature={newFlag}
                  readOnly={readOnly}
                  createFeaturePermission={createFeaturePermission}
                />

                <FeaturesList
                  projectId={projectId}
                  environmentId={environmentId}
                  numericEnvironmentId={numericEnvironmentId}
                  environment={environment}
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
              showEmptyState &&
              createFeaturePermission((perm) => (
                <FeaturesEmptyState
                  environmentId={environmentId}
                  projectId={projectId}
                  onCreateFeature={newFlag}
                  canCreateFeature={perm}
                />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}

const FeaturesPage = ConfigProvider(FeaturesPageComponent)

export default FeaturesPage
