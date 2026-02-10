import React, { FC, useEffect, useState } from 'react'
import { Link, useHistory, useRouteMatch } from 'react-router-dom'
import { useRouteContext } from 'components/providers/RouteContext'
import keyBy from 'lodash/keyBy'

import { getStore } from 'common/store'
import { getTags } from 'common/services/useTag'
import {
  FeatureState,
  Identity,
  IdentityFeatureState,
  IdentityTrait,
  ProjectFlag,
} from 'common/types/responses'
import API from 'project/api'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import Button from 'components/base/forms/Button'
import CodeHelp from 'components/CodeHelp'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import CreateSegmentModal from 'components/modals/CreateSegment'
import EditIdentity from 'components/EditIdentity'
import FeatureListStore from 'common/stores/feature-list-store'
import IdentifierString from 'components/IdentifierString'
import IdentityProvider from 'common/providers/IdentityProvider'
import InfoMessage from 'components/InfoMessage'
import JSONReference from 'components/JSONReference'
import PageTitle from 'components/PageTitle'
import Panel from 'components/base/grid/Panel'
import PanelSearch from 'components/PanelSearch'
import TryIt from 'components/TryIt'
import Utils from 'common/utils/utils'
import _data from 'common/data/base/_data'
import { removeIdentity } from './UsersPage'
import IdentityTraits from 'components/IdentityTraits'
import { useGetIdentitySegmentsQuery } from 'common/services/useIdentitySegment'
import useDebouncedSearch from 'common/useDebouncedSearch'
import FeatureOverrideRow from 'components/feature-override/FeatureOverrideRow'
import FeatureFilters, {
  FiltersValue,
  parseFiltersFromUrlParams,
  getServerFilter,
  getURLParamsFromFilters,
} from 'components/feature-page/FeatureFilters'
import Project from 'common/project'
import SettingTitle from 'components/SettingTitle'

interface RouteParams {
  environmentId: string
  projectId: string
  id: string
  identity: string
}

const UserPage: FC = () => {
  const match = useRouteMatch<RouteParams>()
  const history = useHistory()
  const params = Utils.fromParam()
  const defaultState = parseFiltersFromUrlParams(params)
  const environmentId = match?.params?.environmentId
  const id = match?.params?.id
  const { projectId } = useRouteContext()

  const [filter, setFilter] = useState<FiltersValue>(defaultState)
  const [actualFlags, setActualFlags] =
    useState<Record<string, IdentityFeatureState>>()
  const preselect = Utils.fromParam().flag
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

  useEffect(() => {
    const { search, sort } = filter
    AppActions.searchFeatures(
      projectId,
      environmentId,
      true,
      search,
      sort,
      getServerFilter(filter),
    )
  }, [filter, environmentId, projectId])

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
    if (!projectId) return
    openModal(
      `Segment - ${segment.name}`,
      <CreateSegmentModal
        segment={segment.id}
        readOnly
        environmentId={environmentId}
        projectId={projectId}
      />,
      'side-modal create-segment-modal',
    )
  }

  const preventAddTrait = !AccountStore.getOrganisation().persist_trait_data
  const showAliases = Utils.getIsEdge()

  const fetchPage = React.useCallback(
    (pageNumber: number) => {
      const { search, sort } = filter
      AppActions.getFeatures(
        projectId,
        environmentId,
        true,
        search,
        sort,
        pageNumber,
        getServerFilter(filter),
      )
    },
    [environmentId, projectId, filter],
  )

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
            return (isLoading || !projectId) &&
              (!identityFlags || !actualFlags || !projectFlags) ? (
              <div className='text-center'>
                <Loader />
              </div>
            ) : (
              <>
                <PageTitle
                  title={
                    <div className='h5'>
                      Identifier:{' '}
                      <span className='fw-normal'>
                        <IdentifierString
                          value={
                            (identity && identity.identity.identifier) || id
                          }
                        />
                      </span>
                      {showAliases && (
                        <h6 className='d-flex mb-0 align-items-end gap-1'>
                          <Tooltip
                            title={
                              <span className='user-select-none'>Alias: </span>
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
                      <div className='text-nowrap fs-regular fw-normal mt-2'>
                        View and manage feature states and traits for this
                        identity.
                      </div>
                    </div>
                  }
                ></PageTitle>
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
                            <FeatureFilters
                              value={filter}
                              projectId={projectId}
                              orgId={AccountStore.getOrganisation()?.id}
                              isLoading={FeatureListStore.isLoading}
                              onChange={(next) => {
                                FeatureListStore.isLoading = true
                                history.replace(
                                  `${
                                    document.location.pathname
                                  }?${Utils.toParam(
                                    getURLParamsFromFilters(next),
                                  )}`,
                                )
                                setFilter(next)
                              }}
                            />
                          }
                          isLoading={FeatureListStore.isLoading}
                          items={projectFlags}
                          renderRow={({ id: featureId, name }, i) => {
                            const identityFlag = identityFlags[featureId]
                            const actualEnabled =
                              actualFlags && actualFlags[name]?.enabled
                            const environmentFlag =
                              (environmentFlags &&
                                environmentFlags[featureId]) ||
                              {}
                            const projectFlag = projectFlags?.find(
                              (p: any) => p.id === environmentFlag.feature,
                            )
                            const actualFlagForFeature =
                              actualFlags?.[name]?.feature?.id === featureId
                                ? actualFlags[name]
                                : undefined
                            const overrideFeatureState = identityFlag
                              ? {
                                  ...identityFlag,
                                  //resolves multivariate value if one is set
                                  feature_state_value:
                                    actualFlagForFeature?.feature_state_value,
                                }
                              : actualFlagForFeature ??
                                environmentFlags[featureId]
                            return (
                              !!projectFlag && (
                                <FeatureOverrideRow
                                  identity={id}
                                  environmentId={environmentId}
                                  identifier={identity?.identity?.identifier}
                                  identityName={identityName}
                                  shouldPreselect={name === preselect}
                                  toggleDataTest={`user-feature-switch-${i}${
                                    actualEnabled ? '-on' : '-off'
                                  }`}
                                  level='identity'
                                  valueDataTest={`user-feature-value-${i}`}
                                  projectFlag={projectFlag}
                                  dataTest={`user-feature-${i}`}
                                  overrideFeatureState={overrideFeatureState}
                                  environmentFeatureState={
                                    environmentFlags[featureId]
                                  }
                                />
                              )
                            )
                          }}
                          renderSearchWithNoResults
                          paging={FeatureListStore.paging}
                          nextPage={() =>
                            fetchPage(FeatureListStore.paging.next)
                          }
                          prevPage={() =>
                            fetchPage(FeatureListStore.paging.previous)
                          }
                          goToPage={(pageNumber: number) =>
                            fetchPage(pageNumber)
                          }
                        />
                      </FormGroup>
                      {!preventAddTrait && (
                        <IdentityTraits
                          environmentId={environmentId}
                          projectId={projectId}
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
                    <FormGroup className='mt-5'>
                      <SettingTitle danger>Delete Identity</SettingTitle>
                      <FormGroup className='mt-4'>
                        <p className='fs-small col-lg-8 lh-sm'>
                          Deleting this identity will delete all of their stored
                          traits, and any identity overrides that you have
                          configured. The identity will be recreated if it is
                          identified when identified via your Flagsmith
                          integration again. You can also recreate it in the
                          dashboard from the{' '}
                          <Link
                            to={`/project/${projectId}/environment/${environmentId}/users`}
                          >
                            Identities Page
                          </Link>
                          .
                        </p>
                        <Button
                          id='delete-identity-btn'
                          onClick={() => {
                            removeIdentity(
                              id,
                              (identity && identity.identity.identifier) || id,
                              environmentId,
                              () => {
                                history.replace(
                                  `/project/${projectId}/environment/${environmentId}/users`,
                                )
                              },
                            )
                          }}
                          theme='danger'
                        >
                          Delete Identity
                        </Button>
                      </FormGroup>
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
