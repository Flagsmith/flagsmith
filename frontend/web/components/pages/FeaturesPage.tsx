import React, { FC, useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, useHistory } from 'react-router-dom'
import CreateFlagModal from 'components/modals/CreateFlag'
import ProjectStore from 'common/stores/project-store'
import Permission from 'common/providers/Permission'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import { useRouteContext } from 'components/providers/RouteContext'
import {
  FeaturesEmptyState,
  FeatureMetricsSection,
  FeaturesPageHeader,
  FeaturesList,
  FeaturesSDKIntegration,
} from './features'
import { useGetFeatureListQuery } from 'common/services/useFeatureList'
import { useFeatureFilters } from './features/hooks/useFeatureFilters'
import { useFeatureActions } from './features/hooks/useFeatureActions'

type RouteParams = {
  environmentId: string
  projectId: string
}

const FeaturesPageComponent: FC = () => {
  const { environmentId, projectId } = useParams<RouteParams>()
  const history = useHistory()
  const routeContext = useRouteContext()

  const numericEnvironmentId = useMemo(
    () => ProjectStore.getEnvironmentIdFromKey(environmentId),
    [environmentId],
  )

  // Custom hooks for state management
  const {
    clearFilters,
    filters,
    goToPage,
    handleFilterChange,
    hasFilters,
    page,
  } = useFeatureFilters(history)

  const { forceMetricsRefetch, removeFlag, toggleFlag } = useFeatureActions(
    projectId,
    environmentId,
  )

  const [loadedOnce, setLoadedOnce] = useState(false)

  // RTK Query for data fetching
  const { data, isFetching, isLoading } = useGetFeatureListQuery(
    {
      environmentId: numericEnvironmentId?.toString() || '',
      group_owners: filters.group_owners.length
        ? filters.group_owners.join(',')
        : undefined,
      is_archived: filters.showArchived,
      is_enabled: filters.is_enabled,
      owners: filters.owners.length ? filters.owners.join(',') : undefined,
      page,
      page_size: 50,
      projectId,
      search: filters.search,
      sort_direction: filters.sort.sortOrder === 'asc' ? 'ASC' : 'DESC',
      sort_field: filters.sort.sortBy,
      tag_strategy: filters.tag_strategy,
      tags: filters.tags.length ? filters.tags.join(',') : undefined,
      value_search: filters.value_search || undefined,
    },
    {
      skip: !numericEnvironmentId || !projectId,
    },
  )

  const projectFlags = data?.results || []
  const environmentFlags = data?.environmentStates || {}
  const paging = data?.pagination
  const totalFeatures = data?.count || 0

  // Track page load
  useEffect(() => {
    API.trackPage(Constants.pages.FEATURES)
    AsyncStorage.setItem(
      'lastEnv',
      JSON.stringify({
        environmentId,
        orgId: AccountStore.getOrganisation()?.id,
        projectId,
      }),
    )
  }, [environmentId, projectId])

  // Mark as loaded once data arrives
  useEffect(() => {
    if (data && !loadedOnce) {
      setLoadedOnce(true)
    }
  }, [data, loadedOnce])

  const newFlag = useCallback(() => {
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
    (el: (permission: boolean) => React.ReactNode) => {
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
  const environment = ProjectStore.getEnvironment(environmentId)

  const maxFeaturesAllowed = routeContext.projectId
    ? ProjectStore.getMaxFeaturesAllowed(routeContext.projectId)
    : null

  const showInitialLoader =
    (isLoading || !loadedOnce) && (!projectFlags || !projectFlags.length)
  const showContent =
    loadedOnce ||
    ((filters.showArchived ||
      typeof filters.search === 'string' ||
      !!filters.tags.length) &&
      !isLoading)
  const showEmptyState = !isLoading && loadedOnce && !showContent

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
                  forceRefetch={forceMetricsRefetch}
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
