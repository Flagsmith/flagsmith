import React, { FC, useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, useHistory } from 'react-router-dom'
import { isEqual } from 'lodash'
import classNames from 'classnames'
import CreateFlagModal from 'components/modals/CreateFlag'
import TryIt from 'components/TryIt'
import FeatureRow from 'components/feature-summary/FeatureRow'
import ProjectStore from 'common/stores/project-store'
import Permission from 'common/providers/Permission'
import JSONReference from 'components/JSONReference'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import PageTitle from 'components/PageTitle'
import Format from 'common/utils/format'
import EnvironmentDocumentCodeHelp from 'components/EnvironmentDocumentCodeHelp'
import { useRouteContext } from 'components/providers/RouteContext'
import {
  FeaturesEmptyState,
  FeatureMetricsSection,
  FeaturesTableFilters,
} from './features'
import { useGetFeatureListQuery } from 'common/services/useFeatureList'
import { useRemoveProjectFlagMutation } from 'common/services/useProjectFlag'
import { useUpdateFeatureStateMutation } from 'common/services/useFeatureList'
import type { FilterState } from './features/components/FeaturesTableFilters'

// Global declarations for Bullet Train globals
declare const Utils: any
declare const API: any
declare const AsyncStorage: any
declare const AccountStore: any
declare const openModal: any
declare const toast: any
declare const Loader: any
declare const Button: any
declare const Tooltip: any
declare const FormGroup: any
declare const PanelSearch: any
declare const CodeHelp: any

type RouteParams = {
  environmentId: string
  projectId: string
}

const getFiltersFromParams = (params: any) => {
  return {
    group_owners:
      typeof params.group_owners === 'string'
        ? params.group_owners.split(',').map((v: string) => parseInt(v))
        : [],
    is_enabled: (() => {
      if (params.is_enabled === 'true') return true
      if (params.is_enabled === 'false') return false
      return null
    })(),
    owners:
      typeof params.owners === 'string'
        ? params.owners.split(',').map((v: string) => parseInt(v))
        : [],
    page: params.page ? parseInt(params.page) : 1,
    search: params.search || null,
    showArchived: params.is_archived === 'true',
    sort: {
      label: Format.camelCase(params.sortBy || 'Name'),
      sortBy: params.sortBy || 'name',
      sortOrder: params.sortOrder || 'asc',
    },
    tag_strategy: params.tag_strategy || 'INTERSECTION',
    tags:
      typeof params.tags === 'string'
        ? params.tags.split(',').map((v: string) => parseInt(v))
        : [],
    value_search:
      typeof params.value_search === 'string' ? params.value_search : '',
  }
}

const FeaturesPageComponent: FC = () => {
  const { environmentId, projectId } = useParams<RouteParams>()
  const history = useHistory()
  const routeContext = useRouteContext()

  const numericEnvironmentId = useMemo(
    () => ProjectStore.getEnvironmentIdFromKey(environmentId),
    [environmentId],
  )

  // Initialize filters from URL params
  const initialFilters = useMemo(
    () => getFiltersFromParams(Utils.fromParam()),
    [],
  )

  const [filters, setFilters] = useState<FilterState>(initialFilters)
  const [page, setPage] = useState<number>(initialFilters.page)
  const [forceMetricsRefetch, setForceMetricsRefetch] = useState(false)
  const [loadedOnce, setLoadedOnce] = useState(false)

  // RTK Query hooks
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

  const [removeProjectFlag] = useRemoveProjectFlagMutation()
  const [updateFeatureState] = useUpdateFeatureStateMutation()

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

  // Update URL params when filters change
  const updateURLParams = useCallback(() => {
    const currentParams = Utils.fromParam()
    if (!currentParams.feature) {
      const urlParams = {
        group_owners: filters.group_owners?.join(',') || undefined,
        is_archived: filters.showArchived || undefined,
        is_enabled:
          filters.is_enabled === null ? undefined : filters.is_enabled,
        owners: filters.owners?.join(',') || undefined,
        page: page || 1,
        search: filters.search || '',
        sortBy: filters.sort.sortBy,
        sortOrder: filters.sort.sortOrder,
        tag_strategy: filters.tag_strategy,
        tags: filters.tags?.join(',') || undefined,
        value_search: filters.value_search || undefined,
      }
      history.replace(
        `${document.location.pathname}?${Utils.toParam(urlParams)}`,
      )
    }
  }, [filters, page, history])

  useEffect(() => {
    updateURLParams()
  }, [updateURLParams])

  const toggleForceMetricsRefetch = useCallback(() => {
    setForceMetricsRefetch((prev) => !prev)
  }, [])

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

  const removeFlag = useCallback(
    async (projectId: string, projectFlag: any) => {
      try {
        await removeProjectFlag({
          id: projectFlag.id,
          project: projectId,
        }).unwrap()
        toggleForceMetricsRefetch()
        toast(
          <div>
            Removed feature: <strong>{projectFlag.name}</strong>
          </div>,
        )
      } catch (error) {
        toast('Failed to remove feature', 'danger')
      }
    },
    [removeProjectFlag, toggleForceMetricsRefetch],
  )

  const toggleFlag = useCallback(
    async (
      projectId: string,
      environmentId: string,
      flag: any,
      environmentFlags: any,
    ) => {
      const environmentFlag = environmentFlags[flag.id]
      if (!environmentFlag) return

      try {
        await updateFeatureState({
          body: {
            enabled: !environmentFlag.enabled,
          },
          environmentId,
          stateId: environmentFlag.id,
        }).unwrap()
        toggleForceMetricsRefetch()
      } catch (error) {
        toast('Failed to toggle feature', 'danger')
      }
    },
    [updateFeatureState, toggleForceMetricsRefetch],
  )

  const handleFilterChange = useCallback((updates: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...updates }))
    setPage(1) // Reset to page 1 when filters change
  }, [])

  const clearFilters = useCallback(() => {
    history.replace(document.location.pathname)
    const newFilters = getFiltersFromParams({})
    setFilters(newFilters)
    setPage(1)
  }, [history])

  const goToPage = useCallback((newPage: number) => {
    setPage(newPage)
  }, [])

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
  const params = Utils.fromParam()

  const hasFilters = !isEqual(
    getFiltersFromParams({ ...params, page: '1' }),
    getFiltersFromParams({ page: '1' }),
  )

  const maxFeaturesAllowed = routeContext.projectId
    ? ProjectStore.getMaxFeaturesAllowed(routeContext.projectId)
    : null
  const featureLimitAlert = Utils.calculateRemainingLimitsPercentage(
    totalFeatures,
    maxFeaturesAllowed,
  )

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
                {featureLimitAlert.percentage &&
                  Utils.displayLimitAlert(
                    'features',
                    featureLimitAlert.percentage,
                  )}
                <FeatureMetricsSection
                  environmentApiKey={environment?.api_key}
                  forceRefetch={forceMetricsRefetch}
                  projectId={projectId}
                />
                <PageTitle
                  title={'Features'}
                  cta={
                    <>
                      {loadedOnce ||
                      filters.showArchived ||
                      filters.tags?.length
                        ? createFeaturePermission((perm) => (
                            <Button
                              disabled={
                                !perm ||
                                readOnly ||
                                featureLimitAlert.percentage >= 100
                              }
                              className='w-100'
                              data-test='show-create-feature-btn'
                              id='show-create-feature-btn'
                              onClick={newFlag}
                            >
                              Create Feature
                            </Button>
                          ))
                        : null}
                    </>
                  }
                >
                  View and manage{' '}
                  <Tooltip
                    title={
                      <Button className='fw-normal' theme='text'>
                        feature flags
                      </Button>
                    }
                    place='right'
                  >
                    {Constants.strings.FEATURE_FLAG_DESCRIPTION}
                  </Tooltip>{' '}
                  and{' '}
                  <Tooltip
                    title={
                      <Button className='fw-normal' theme='text'>
                        remote config
                      </Button>
                    }
                    place='right'
                  >
                    {Constants.strings.REMOTE_CONFIG_DESCRIPTION}
                  </Tooltip>{' '}
                  for your selected environment.
                </PageTitle>
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
                        onFilterChange={handleFilterChange}
                        onClearFilters={clearFilters}
                      />
                    }
                    nextPage={() => paging?.next && goToPage(page + 1)}
                    prevPage={() => paging?.previous && goToPage(page - 1)}
                    goToPage={goToPage}
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
                          json={
                            environmentFlags && Object.values(environmentFlags)
                          }
                        />
                      </>
                    )}
                    renderRow={(projectFlag, i) => (
                      <Permission
                        level='environment'
                        tags={projectFlag.tags}
                        permission={Utils.getManageFeaturePermission(
                          Utils.changeRequestsEnabled(
                            environment &&
                              environment.minimum_change_request_approvals,
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
                            toggleFlag={toggleFlag}
                            removeFlag={removeFlag}
                            projectFlag={projectFlag}
                          />
                        )}
                      </Permission>
                    )}
                  />
                </FormGroup>
                <FormGroup className='mt-5'>
                  <CodeHelp
                    title='1: Installing the SDK'
                    snippets={Constants.codeHelp.INSTALL}
                  />
                  <CodeHelp
                    title='2: Initialising your project'
                    snippets={Constants.codeHelp.INIT(
                      environmentId,
                      projectFlags?.[0]?.name,
                    )}
                  />
                  <EnvironmentDocumentCodeHelp
                    title='3: Providing feature defaults and support offline'
                    projectId={projectId}
                    environmentId={environmentId}
                  />
                </FormGroup>
                <FormGroup className='pb-4'>
                  <TryIt
                    title='Test what values are being returned from the API on this environment'
                    environmentId={environmentId}
                  />
                </FormGroup>
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
