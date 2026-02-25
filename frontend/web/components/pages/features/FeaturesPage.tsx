import React, { FC, useCallback, useEffect, useMemo } from 'react'
import { useHistory } from 'react-router-dom'
import CreateFlagModal from 'components/modals/create-feature'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import AppActions from 'common/dispatcher/app-actions'
import FeatureListStore from 'common/stores/feature-list-store'
import { FEATURES_PAGE_SIZE } from 'common/services/useProjectFlag'
import { useRouteContext } from 'components/providers/RouteContext'
import { usePageTracking } from 'common/hooks/usePageTracking'
import FeatureRow from 'components/feature-summary/FeatureRow'
import FeatureRowSkeleton from 'components/feature-summary/FeatureRowSkeleton'
import JSONReference from 'components/JSONReference'
import Permission from 'common/providers/Permission'
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
import { useFeatureListWithApiKey } from 'common/hooks/useFeatureListWithApiKey'
import { useViewMode } from 'common/useViewMode'
import type { Pagination } from './types'
import type { ProjectFlag, FeatureState } from 'common/types/responses'

const DEFAULT_PAGINATION: Pagination = {
  count: 0,
  currentPage: 1,
  next: null,
  pageSize: FEATURES_PAGE_SIZE,
  previous: null,
}

const SKELETON_ITEMS = Array(10).fill({ isSkeleton: true })

type SkeletonItem = { isSkeleton: boolean }

function isSkeletonItem(
  item: ProjectFlag | SkeletonItem,
): item is SkeletonItem {
  return 'isSkeleton' in item && item.isSkeleton === true
}

type FeaturesPageProps = {
  pageTitle?: string
  forcedTagIds?: number[]
  defaultExperiment?: boolean
}

const FeaturesPage: FC<FeaturesPageProps> = ({
  defaultExperiment,
  forcedTagIds,
  pageTitle,
}) => {
  const history = useHistory()
  const routeContext = useRouteContext()
  const projectId = routeContext.projectId!
  const environmentId = routeContext.environmentId!
  const {
    clearFilters,
    filters,
    goToPage,
    handleFilterChange,
    hasFilters,
    page,
  } = useFeatureFilters(history)

  const {
    isCompact,
    setViewMode: handleViewModeChange,
    viewMode,
  } = useViewMode()

  const effectiveFilters = useMemo(() => {
    if (!forcedTagIds) return filters
    const mergedTags = [...new Set([...(filters.tags || []), ...forcedTagIds])]
    return { ...filters, tags: mergedTags }
  }, [filters, forcedTagIds])

  const {
    error: projectEnvError,
    getEnvironment,
    project,
  } = useProjectEnvironments(projectId)
  const { data, error, isFetching, isLoading, refetch } =
    useFeatureListWithApiKey(effectiveFilters, page, environmentId, projectId)

  // Backward compatibility: Populate ProjectStore for legacy components (CreateFlag)
  // TODO: Remove this when CreateFlag is migrated to RTK Query
  useEffect(() => {
    if (projectId) {
      AppActions.getProject(projectId)
    }
  }, [projectId])

  // Backward compatibility: Populate FeatureListStore for legacy components (CreateFlag modal)
  // Must pass current filters/search/page so FeatureListStore contains the same features
  // that RTK Query displays. Otherwise editing features will crash because they're not in the store.
  // TODO: Remove this when CreateFlag is migrated to RTK Query
  useEffect(() => {
    if (projectId && environmentId) {
      AppActions.getFeatures(
        projectId,
        environmentId,
        true,
        effectiveFilters.search,
        effectiveFilters.sort,
        page,
        {
          group_owners: effectiveFilters.group_owners?.join(',') || undefined,
          is_archived: effectiveFilters.showArchived,
          is_enabled: effectiveFilters.is_enabled,
          owners: effectiveFilters.owners?.join(',') || undefined,
          tag_strategy: effectiveFilters.tag_strategy,
          tags: effectiveFilters.tags?.join(',') || undefined,
          value_search: effectiveFilters.value_search,
        },
      )
    }
  }, [projectId, environmentId, page, effectiveFilters])

  // Force re-fetch when legacy Flux store updates features
  // TODO: Remove when all feature mutations use RTK Query
  useEffect(() => {
    const onFeatureListChange = () => {
      // Refetch RTK Query data when Flux store changes
      refetch()
    }
    FeatureListStore.on('saved', onFeatureListChange)
    FeatureListStore.on('removed', onFeatureListChange)
    return () => {
      FeatureListStore.off('saved', onFeatureListChange)
      FeatureListStore.off('removed', onFeatureListChange)
    }
  }, [refetch])

  const currentEnvironment = getEnvironment(environmentId)
  const minimumChangeRequestApprovals =
    currentEnvironment?.minimum_change_request_approvals

  const [removeFeature] = useRemoveFeatureWithToast()
  const [toggleFeature] = useToggleFeatureWithToast()

  const removeFlag = useCallback(
    async (projectFlag: ProjectFlag) => {
      await removeFeature(projectFlag, projectId)
    },
    [removeFeature, projectId],
  )

  const toggleFlag = useCallback(
    async (
      flag: ProjectFlag,
      environmentFlag: FeatureState | undefined,
      onError?: () => void,
    ) => {
      if (!currentEnvironment) {
        onError?.()
        return
      }
      await toggleFeature(flag, environmentFlag, currentEnvironment, {
        onError,
      })
    },
    [toggleFeature, currentEnvironment],
  )

  const projectFlags = useMemo(() => data?.results ?? [], [data?.results])
  const environmentFlags = useMemo(
    () => data?.environmentStates ?? {},
    [data?.environmentStates],
  )
  const paging = useMemo(
    () => data?.pagination ?? DEFAULT_PAGINATION,
    [data?.pagination],
  )

  usePageTracking({
    context: {
      environmentId,
      organisationId: routeContext.organisationId,
      projectId,
    },
    pageName: Constants.pages.FEATURES,
    saveToStorage: true,
  })

  const openNewFlagModal = () => {
    openModal(
      'New Feature',
      <CreateFlagModal
        environmentId={environmentId}
        history={history}
        projectId={projectId}
        defaultExperiment={defaultExperiment}
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
        orgId={project?.organisation}
        onFilterChange={handleFilterChange}
        onClearFilters={clearFilters}
        viewMode={viewMode}
        onViewModeChange={handleViewModeChange}
      />
    ),
    [
      projectId,
      filters,
      hasFilters,
      isLoading,
      project?.organisation,
      handleFilterChange,
      clearFilters,
      viewMode,
      handleViewModeChange,
    ],
  )

  const renderFooter = useCallback(
    () => (
      <>
        <JSONReference
          className='mx-2 mt-4'
          showNamesButton
          title='Features'
          json={projectFlags}
        />
        <JSONReference
          className='mx-2'
          title='Feature States'
          json={environmentFlags && Object.values(environmentFlags)}
        />
      </>
    ),
    [projectFlags, environmentFlags],
  )

  const renderFeatureRow = useCallback(
    (projectFlag: ProjectFlag | SkeletonItem, i: number) => {
      if (isSkeletonItem(projectFlag)) {
        return <FeatureRowSkeleton key={`skeleton-${i}`} />
      }

      return (
        <Permission
          key={projectFlag.id}
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
              isCompact={isCompact}
              experimentMode={defaultExperiment}
            />
          )}
        </Permission>
      )
    },
    [
      environmentFlags,
      environmentId,
      projectId,
      minimumChangeRequestApprovals,
      toggleFlag,
      removeFlag,
      isCompact,
      defaultExperiment,
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

  const renderFeaturesList = () => {
    const shouldShowEmptyState =
      data && projectFlags.length === 0 && !hasFilters && !isFetching

    if (!shouldShowEmptyState) {
      return (
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
          items={!data ? SKELETON_ITEMS : projectFlags}
          renderFooter={renderFooter}
          renderRow={renderFeatureRow}
        />
      )
    }

    return (
      <Permission
        level='project'
        permission='CREATE_FEATURE'
        id={projectId}
        showTooltip
        permissionName='Create Feature'
      >
        {({ permission: perm }) => (
          <FeaturesEmptyState
            environmentId={environmentId}
            projectId={projectId}
            onCreateFeature={openNewFlagModal}
            canCreateFeature={perm}
          />
        )}
      </Permission>
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
        {error || projectEnvError ? (
          <div className='text-center'>
            <h4 className='mb-3'>Unable to Load Features</h4>
            <p className='text-muted mb-3'>
              We couldn't load your feature flags. This might be due to a
              network issue or a temporary server problem.
            </p>
          </div>
        ) : (
          <>
            <FeatureMetricsSection
              environmentId={environmentId}
              projectId={projectId}
            />

            <FeaturesPageHeader
              onCreateFeature={openNewFlagModal}
              readOnly={readOnly}
              projectId={projectId}
              title={pageTitle}
            />

            <FormGroup className='mb-4'>{renderFeaturesList()}</FormGroup>

            <FeaturesSDKIntegration
              projectId={projectId}
              environmentId={environmentId}
            />
          </>
        )}
      </div>
    </div>
  )
}

export default FeaturesPage
