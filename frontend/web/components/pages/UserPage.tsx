import React, { FC, useCallback, useEffect, useState } from 'react'
import { useHistory, useRouteMatch } from 'react-router-dom'
import { useRouteContext } from 'components/providers/RouteContext'
import keyBy from 'lodash/keyBy'

import { getStore } from 'common/store'
import { getTags } from 'common/services/useTag'
import { getViewMode, setViewMode } from 'common/useViewMode'
import { removeUserOverride } from 'components/RemoveUserOverride'
import {
  FeatureState,
  Identity,
  IdentityFeatureState,
  IdentityTrait,
  ProjectFlag,
  TagStrategy,
} from 'common/types/responses'
import API from 'project/api'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import Button from 'components/base/forms/Button'
import CodeHelp from 'components/CodeHelp'
import ConfigProvider from 'common/providers/ConfigProvider'
import ConfirmToggleFeature from 'components/modals/ConfirmToggleFeature'
import Constants from 'common/constants'
import CreateFlagModal from 'components/modals/CreateFlag'
import CreateSegmentModal from 'components/modals/CreateSegment'
import EditIdentity from 'components/EditIdentity'
import FeatureListStore from 'common/stores/feature-list-store'
import Format from 'common/utils/format'
import Icon from 'components/Icon'
import IdentifierString from 'components/IdentifierString'
import IdentityProvider from 'common/providers/IdentityProvider'
import InfoMessage from 'components/InfoMessage'
import JSONReference from 'components/JSONReference'
import PageTitle from 'components/PageTitle'
import Panel from 'components/base/grid/Panel'
import PanelSearch from 'components/PanelSearch'
import Permission, { useHasPermission } from 'common/providers/Permission'
// @ts-ignore
import Project from 'common/project'
import TableFilterOptions from 'components/tables/TableFilterOptions'
import TableGroupsFilter from 'components/tables/TableGroupsFilter'
import TableOwnerFilter from 'components/tables/TableOwnerFilter'
import TableSearchFilter from 'components/tables/TableSearchFilter'
import TableSortFilter, { SortValue } from 'components/tables/TableSortFilter'
import TableTagFilter from 'components/tables/TableTagFilter'
import TableValueFilter from 'components/tables/TableValueFilter'
import TryIt from 'components/TryIt'
import Utils from 'common/utils/utils'
// @ts-ignore
import _data from 'common/data/base/_data'
import { removeIdentity } from './UsersPage'
import { isEqual } from 'lodash'
import ClearFilters from 'components/ClearFilters'
import IdentityTraits from 'components/IdentityTraits'
import { useGetIdentitySegmentsQuery } from 'common/services/useIdentitySegment'
import useDebouncedSearch from 'common/useDebouncedSearch'
import FeatureOverrideRow from 'components/feature-override/FeatureOverrideRow'
import featureValuesEqual from 'common/featureValuesEqual'

interface RouteParams {
  environmentId: string
  projectId: string
  id: string
  identity: string
}

type FeatureFilter = {
  group_owners: number[]
  is_archived: boolean
  is_enabled: boolean | null
  owners: number[]
  tag_strategy: TagStrategy
  tags: (number | string)[]
  value_search: string | null
  search: string | null
  sort: SortValue
}

const getFiltersFromParams = (params: Record<string, string | undefined>) =>
  ({
    group_owners:
      typeof params.group_owners === 'string'
        ? params.group_owners.split(',').map((v: string) => parseInt(v))
        : [],
    is_archived: params.is_archived === 'true',
    is_enabled:
      params.is_enabled === 'true'
        ? true
        : params.is_enabled === 'false'
        ? false
        : null,
    owners:
      typeof params.owners === 'string'
        ? params.owners.split(',').map((v: string) => parseInt(v))
        : [],
    search: params.search || null,
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
    value_search: params.value_search || '',
  } as FeatureFilter)

const UserPage: FC = () => {
  const match = useRouteMatch<RouteParams>()
  const history = useHistory()

  const params = Utils.fromParam()
  const defaultState = getFiltersFromParams(params)

  const environmentId = match?.params?.environmentId
  const id = match?.params?.id
  const identity = match?.params?.identity
  const { projectId } = useRouteContext()

  const [filter, setFilter] = useState(defaultState)
  const [actualFlags, setActualFlags] =
    useState<Record<string, IdentityFeatureState>>()
  const [preselect, setPreselect] = useState(Utils.fromParam().flag)
  const [segmentsPage, setSegmentsPage] = useState(1)
  const { search, searchInput, setSearchInput } = useDebouncedSearch('')
  const { data: segments, isFetching: isFetchingSegments } =
    useGetIdentitySegmentsQuery(
      {
        identity: id,
        page: segmentsPage,
        page_size: 10,
        projectId: `${projectId}`,
        q: search,
      },
      { skip: !projectId },
    )
  const getFilter = useCallback(
    (filter) => ({
      ...filter,
      group_owners: filter.group_owners.length
        ? filter.group_owners
        : undefined,
      owners: filter.owners.length ? filter.owners : undefined,
      search: (filter.search || '').trim(),
      tags: filter.tags.length ? filter.tags.join(',') : undefined,
    }),
    [],
  )

  const hasFilters = !isEqual(
    getFilter({ ...filter, search: filter.search || null }),
    getFilter(getFiltersFromParams({})),
  )

  useEffect(() => {
    const { search, sort, ...rest } = getFilter(filter)
    AppActions.searchFeatures(
      projectId,
      environmentId,
      true,
      search,
      sort,
      rest,
    )
  }, [filter, getFilter, environmentId, projectId])

  useEffect(() => {
    AppActions.getIdentity(environmentId, id)
    getTags(getStore(), { projectId: `${projectId}` })
    getActualFlags()
    API.trackPage(Constants.pages.USER)
    // eslint-disable-next-line
  }, [])

  const getActualFlags = () => {
    const url = `${
      Project.api
    }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${id}/${Utils.getFeatureStatesEndpoint()}/all/`
    _data.get(url).then((res: IdentityFeatureState[]) => {
      setActualFlags(keyBy(res, (v: IdentityFeatureState) => v.feature.name))
    })
  }

  const onSave = () => {
    getActualFlags()
  }

  const editSegment = (segment: any) => {
    API.trackEvent(Constants.events.VIEW_SEGMENT)
    openModal(
      `Segment - ${segment.name}`,
      <CreateSegmentModal
        segment={segment.id}
        readOnly
        environmentId={environmentId}
        projectId={projectId!}
      />,
      'side-modal create-segment-modal',
    )
  }

  const preventAddTrait = !AccountStore.getOrganisation().persist_trait_data
  const isEdge = Utils.getIsEdge()
  const showAliases = isEdge && Utils.getFlagsmithHasFeature('identity_aliases')
  const clearFilters = () => {
    history.replace(`${document.location.pathname}`)
    setFilter(getFiltersFromParams({}))
  }

  return (
    <div className='app-container container'>
      <div>
        <IdentityProvider onSave={onSave}>
          {({
            environmentFlags,
            identity,
            identityFlags,
            isLoading,
            projectFlags,
          }: {
            environmentFlags: FeatureState[]
            identity: { identity: Identity; identifier: string }
            identityFlags: IdentityFeatureState[]
            isLoading: boolean
            projectFlags: ProjectFlag[]
            traits: IdentityTrait[]
          }) => {
            const identityName =
              (identity && identity.identity.identifier) || id

            return isLoading &&
              !filter.tags.length &&
              !filter.is_archived &&
              typeof filter.search !== 'string' &&
              (!identityFlags || !actualFlags || !projectFlags) ? (
              <div className='text-center'>
                <Loader />
              </div>
            ) : (
              <>
                <PageTitle
                  title={
                    <div className='d-flex align-items-center justify-content-between'>
                      <div>
                        <IdentifierString value={identityName} />
                        {showAliases && (
                          <h6 className='d-flex align-items-center gap-1'>
                            <Tooltip
                              title={
                                <span className='user-select-none'>
                                  Alias:{' '}
                                </span>
                              }
                            >
                              Aliases allow you to add searchable names to an
                              identity
                            </Tooltip>
                            {!!identity && (
                              <EditIdentity
                                data={identity?.identity}
                                environmentId={environmentId}
                              />
                            )}
                          </h6>
                        )}
                      </div>
                      <Button
                        id='remove-feature'
                        className='btn btn-with-icon'
                        type='button'
                        onClick={() => {
                          removeIdentity(
                            id,
                            identityName,
                            environmentId,
                            () => {
                              history.replace(
                                `/project/${projectId}/environment/${environmentId}/users`,
                              )
                            },
                          )
                        }}
                      >
                        <Icon name='trash-2' width={20} fill='#656D7B' />
                      </Button>
                    </div>
                  }
                >
                  View and manage feature states and traits for this user.
                  <br />
                </PageTitle>
                <div className='row'>
                  <div className='col-md-12'>
                    <FormGroup>
                      <FormGroup>
                        <PanelSearch
                          id='user-features-list'
                          className='no-pad overflow-visible'
                          itemHeight={70}
                          title={
                            <div>
                              Features
                              <div className='fw-normal mt-2 fs-medium'>
                                <InfoMessage collapseId={'identity-priority'}>
                                  Overriding features here will take priority
                                  over any segment override. Any features that
                                  are not overridden for this user will fallback
                                  to any segment overrides or the environment
                                  defaults.
                                </InfoMessage>
                              </div>
                            </div>
                          }
                          renderFooter={() => (
                            <>
                              <JSONReference
                                showNamesButton
                                className='mt-4 mx-2'
                                title={'Features'}
                                json={
                                  projectFlags && Object.values(projectFlags)
                                }
                              />
                              <JSONReference
                                className='mx-2'
                                title={'Environment Feature States'}
                                json={
                                  environmentFlags &&
                                  Object.values(environmentFlags)
                                }
                              />
                              <JSONReference
                                className='mx-2'
                                title={'Identity Feature States'}
                                json={
                                  identityFlags && Object.values(identityFlags)
                                }
                              />
                            </>
                          )}
                          header={
                            <Row className='table-header'>
                              <div className='table-column flex-row flex-fill'>
                                <TableSearchFilter
                                  onChange={(e) => {
                                    FeatureListStore.isLoading = true
                                    setFilter({
                                      ...filter,
                                      search: Utils.safeParseEventValue(e),
                                    })
                                  }}
                                  value={filter.search}
                                />
                                <Row className='flex-fill justify-content-end'>
                                  {hasFilters && (
                                    <ClearFilters onClick={clearFilters} />
                                  )}
                                  <TableTagFilter
                                    projectId={projectId!}
                                    className='me-4'
                                    value={filter.tags}
                                    tagStrategy={filter.tag_strategy}
                                    onChangeStrategy={(tag_strategy) => {
                                      setFilter({
                                        ...filter,
                                        tag_strategy,
                                      })
                                    }}
                                    isLoading={FeatureListStore.isLoading}
                                    onToggleArchived={(value) => {
                                      if (value !== filter.is_archived) {
                                        FeatureListStore.isLoading = true
                                        setFilter({
                                          ...filter,
                                          is_archived: !filter.is_archived,
                                        })
                                      }
                                    }}
                                    showArchived={filter.is_archived}
                                    onChange={(newTags) => {
                                      FeatureListStore.isLoading = true
                                      setFilter({
                                        ...filter,
                                        tags:
                                          newTags.includes('') &&
                                          newTags.length > 1
                                            ? ['']
                                            : newTags,
                                      })
                                    }}
                                  />
                                  <TableValueFilter
                                    className='me-4'
                                    value={{
                                      enabled: filter.is_enabled,
                                      valueSearch: filter.value_search,
                                    }}
                                    onChange={({ enabled, valueSearch }) => {
                                      setFilter({
                                        ...filter,
                                        is_enabled: enabled,
                                        value_search: valueSearch,
                                      })
                                    }}
                                  />
                                  <TableOwnerFilter
                                    className={'me-4'}
                                    value={filter.owners}
                                    onChange={(owners) => {
                                      FeatureListStore.isLoading = true
                                      setFilter({
                                        ...filter,
                                        owners,
                                      })
                                    }}
                                  />
                                  <TableGroupsFilter
                                    className={'me-4'}
                                    orgId={AccountStore.getOrganisation()?.id}
                                    value={filter.group_owners}
                                    onChange={(group_owners) => {
                                      FeatureListStore.isLoading = true
                                      setFilter({
                                        ...filter,
                                        group_owners,
                                      })
                                    }}
                                  />
                                  <TableFilterOptions
                                    title={'View'}
                                    className={'me-4'}
                                    value={getViewMode()}
                                    onChange={setViewMode as any}
                                    options={[
                                      {
                                        label: 'Default',
                                        value: 'default',
                                      },
                                      {
                                        label: 'Compact',
                                        value: 'compact',
                                      },
                                    ]}
                                  />
                                  <TableSortFilter
                                    value={filter.sort}
                                    isLoading={FeatureListStore.isLoading}
                                    options={[
                                      {
                                        label: 'Name',
                                        value: 'name',
                                      },
                                      {
                                        label: 'Created Date',
                                        value: 'created_date',
                                      },
                                    ]}
                                    onChange={(sort) => {
                                      FeatureListStore.isLoading = true
                                      setFilter({
                                        ...filter,
                                        sort,
                                      })
                                    }}
                                  />
                                </Row>
                              </div>
                            </Row>
                          }
                          isLoading={FeatureListStore.isLoading}
                          items={projectFlags}
                          renderRow={({ id: featureId, name, tags }, i) => {
                            const identityFlag = identityFlags[featureId] || {}
                            const actualEnabled =
                              actualFlags && actualFlags[name]?.enabled
                            const environmentFlag =
                              (environmentFlags &&
                                environmentFlags[featureId]) ||
                              {}
                            const projectFlag = projectFlags?.find(
                              (p: any) => p.id === environmentFlag.feature,
                            )
                            return (
                              !!projectFlag && (
                                <FeatureOverrideRow
                                  identity={id}
                                  identityName={identityName}
                                  shouldPreselect={name === preselect}
                                  toggleDataTest={`user-feature-switch-${i}${
                                    actualEnabled ? '-on' : '-off'
                                  }`}
                                  level='identity'
                                  valueDataTest={`user-feature-value-${i}`}
                                  projectFlag={projectFlag}
                                  dataTest={`user-feature-${i}`}
                                  overrideFeatureState={
                                    identityFlag || actualFlags?.[name]
                                  }
                                  environmentFeatureState={
                                    environmentFlags[featureId]
                                  }
                                />
                              )
                            )
                          }}
                          renderSearchWithNoResults
                          paging={FeatureListStore.paging}
                          search={filter.search}
                          nextPage={() =>
                            AppActions.getFeatures(
                              projectId,
                              environmentId,
                              true,
                              filter.search,
                              filter.sort,
                              FeatureListStore.paging.next,
                              getFilter(filter),
                            )
                          }
                          prevPage={() =>
                            AppActions.getFeatures(
                              projectId,
                              environmentId,
                              true,
                              filter.search,
                              filter.sort,
                              FeatureListStore.paging.previous,
                              getFilter(filter),
                            )
                          }
                          goToPage={(pageNumber: number) =>
                            AppActions.getFeatures(
                              projectId,
                              environmentId,
                              true,
                              filter.search,
                              filter.sort,
                              pageNumber,
                              getFilter(filter),
                            )
                          }
                        />
                      </FormGroup>
                      {!preventAddTrait && (
                        <IdentityTraits
                          environmentId={environmentId}
                          projectId={projectId!}
                          identityId={id}
                          identityName={identity?.identity?.identifier || id}
                        />
                      )}{' '}
                      {!segments?.results ? (
                        <div className='text-center'>
                          <Loader />
                        </div>
                      ) : (
                        <FormGroup>
                          <PanelSearch
                            id='user-segments-list'
                            className='no-pad'
                            title='Segments'
                            isLoading={isFetchingSegments}
                            search={searchInput}
                            onChange={(e) => {
                              setSearchInput(Utils.safeParseEventValue(e))
                            }}
                            itemHeight={70}
                            paging={segments}
                            nextPage={() => setSegmentsPage(segmentsPage + 1)}
                            prevPage={() => setSegmentsPage(segmentsPage - 1)}
                            goToPage={setSegmentsPage}
                            header={
                              <Row className='table-header'>
                                <Flex
                                  className='table-column px-3'
                                  style={{ maxWidth: '230px' }}
                                >
                                  Name
                                </Flex>
                                <Flex className='table-column'>
                                  Description
                                </Flex>
                              </Row>
                            }
                            items={segments.results}
                            renderRow={({ description, name }, i) => (
                              <Row
                                className='list-item clickable'
                                space
                                key={i}
                                onClick={() => editSegment(segments.results[i])}
                              >
                                <Flex
                                  className='table-column px-3'
                                  style={{ maxWidth: '230px' }}
                                >
                                  <div
                                    onClick={() =>
                                      editSegment(segments.results[i])
                                    }
                                  >
                                    <span
                                      data-test={`segment-${i}-name`}
                                      className='font-weight-medium'
                                    >
                                      {name}
                                    </span>
                                  </div>
                                </Flex>
                                <Flex className='table-column list-item-subtitle'>
                                  {description && <div>{description}</div>}
                                </Flex>
                              </Row>
                            )}
                            renderNoResults={
                              <Panel title='Segments' className='no-pad'>
                                <div className='search-list'>
                                  <Row className='list-item text-muted px-3'>
                                    This user is not a member of any segments.
                                  </Row>
                                </div>
                              </Panel>
                            }
                            filterRow={({ name }: any, searchString: string) =>
                              name
                                .toLowerCase()
                                .indexOf(searchString.toLowerCase()) > -1
                            }
                          />
                        </FormGroup>
                      )}
                    </FormGroup>
                  </div>
                  <div className='col-md-12 mt-2'>
                    <FormGroup>
                      <CodeHelp
                        title='Managing user traits and segments'
                        snippets={Constants.codeHelp.USER_TRAITS(
                          environmentId,
                          identityName,
                        )}
                      />
                    </FormGroup>
                    <FormGroup>
                      <TryIt
                        title='Check to see what features and traits are coming back for this user'
                        environmentId={environmentId}
                        userId={identityName}
                      />
                    </FormGroup>
                  </div>
                </div>
              </>
            )
          }}
        </IdentityProvider>
      </div>
    </div>
  )
}

export default ConfigProvider(UserPage)
