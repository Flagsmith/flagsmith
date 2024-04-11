import React, { Component, ReactNode, useEffect, useState } from 'react'
import TagFilter from 'components/tags/TagFilter'
import Tag from 'components/tags/Tag'
import FeatureRow from 'components/FeatureRow'
import FeatureListStore from 'common/stores/feature-list-store'
import ProjectStore from 'common/stores/project-store'
import API from 'project/api'
import { getStore } from 'common/store'
import Permission from 'common/providers/Permission'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import { Provider } from 'react-redux'
import InfoMessage from 'components/InfoMessage'
import ProjectProvider from 'common/providers/ProjectProvider'
import AccountProvider from 'common/providers/AccountProvider'
import PanelSearch from 'components/PanelSearch'
// @ts-ignore
import { AsyncStorage } from 'polyfill-react-native'
import {
  Environment,
  FeatureListProviderActions,
  FeatureListProviderData,
  Organisation,
  PagedResponse,
  Project,
  ProjectFlag,
  TagStrategy,
} from 'common/types/responses'
import { useCustomWidgetOptionString } from '@datadog/ui-extensions-react'
import client from 'components/datadog-client'
import { resolveAuthFlow } from '@datadog/ui-extensions-sdk'
import AuditLog from 'components/AuditLog'
import OrgEnvironmentSelect from 'components/OrgEnvironmentSelect'
import AccountStore from 'common/stores/account-store'

const FeatureListProvider = require('common/providers/FeatureListProvider')
const AppActions = require('common/dispatcher/app-actions')
const ES6Component = require('common/ES6Component')
let isWidget = false
export const getIsWidget = () => {
  return isWidget
}

type FeatureListType = {
  projectId: string
  environmentId: string
  pageSize: number
  hideTags: boolean
}

const PermissionError = () => {
  return (
    <InfoMessage>
      Please check you have access to the project and environment within the
      widget settings.
    </InfoMessage>
  )
}

type OrganisationWrapperType = {
  projectId: string | undefined
  children: ReactNode
}
const OrganisationWrapper = class extends Component<OrganisationWrapperType> {
  constructor(props: any, context: any) {
    super(props, context)
    ES6Component(this)
    if (this.props.projectId) {
      AppActions.getProject(this.props.projectId)
    }
  }

  componentDidUpdate(prevProps: Readonly<OrganisationWrapperType>) {
    if (this.props.projectId !== prevProps.projectId && this.props.projectId) {
      AppActions.getProject(this.props.projectId)
    }
  }
  render() {
    if (!this.props.projectId) return <>{this.props.children}</>
    return (
      <AccountProvider>
        {() => (
          <ProjectProvider>
            {() => {
              const project = ProjectStore.model as Project | null
              if (
                project &&
                project?.organisation !== AccountStore.getOrganisation()?.id
              ) {
                // @ts-ignore
                AccountStore.organisation =
                  AccountStore.getOrganisations()?.find(
                    (org: Organisation) => org.id === project.organisation,
                  )
                // @ts-ignore
                if (!AccountStore.organisation) {
                  return null
                }
              }
              // @ts-ignore
              return AccountStore.model && ProjectStore.model ? (
                this.props.children
              ) : (
                <div className='text-center'>
                  <Loader />
                </div>
              )
            }}
          </ProjectProvider>
        )}
      </AccountProvider>
    )
  }
}

const FeatureList = class extends Component<FeatureListType> {
  state = {
    error: null as null | string,
    search: null as null | string,
    showArchived: false,
    sort: { label: 'Name', sortBy: 'name', sortOrder: 'asc' },
    tag_strategy: 'INTERSECTION' as TagStrategy,
    tags: [] as string[],
  }
  constructor(props: any, context: any) {
    super(props, context)
    ES6Component(this)
    AppActions.getFeatures(
      this.props.projectId,
      this.props.environmentId,
      true,
      this.state.search,
      this.state.sort,
      0,
      this.getFilter(),
      this.props.pageSize,
    )
  }

  componentDidUpdate(prevProps: Readonly<FeatureListType>) {
    if (
      this.props.projectId !== prevProps.projectId ||
      this.props.environmentId !== prevProps.environmentId ||
      this.props.pageSize !== prevProps.pageSize
    ) {
      AppActions.getFeatures(
        this.props.projectId,
        this.props.environmentId,
        true,
        this.state.search,
        this.state.sort,
        0,
        this.getFilter(),
        this.props.pageSize,
      )
    }
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.FEATURES)
  }

  getFilter = () => ({
    is_archived: this.state.showArchived,
    tag_strategy: this.state.tag_strategy,
    tags:
      !this.state.tags || !this.state.tags.length
        ? undefined
        : this.state.tags.join(','),
  })

  onSave = () => {
    toast('Saved')
  }

  filter = () => {
    AppActions.searchFeatures(
      this.props.projectId,
      this.props.environmentId,
      true,
      this.state.search,
      this.state.sort,
      this.getFilter(),
      this.props.pageSize,
    )
  }

  render() {
    const { environmentId, projectId } = this.props
    const environment = ProjectStore.getEnvironment(
      environmentId,
    ) as Environment | null
    return (
      <Provider store={getStore()}>
        <div
          className='widget-container'
          data-test='features-page'
          id='features-page'
        >
          <FeatureListProvider onSave={this.onSave}>
            {(
              {
                environmentFlags,
                error,
                isLoading,
                projectFlags,
              }: FeatureListProviderData,
              { removeFlag, toggleFlag }: FeatureListProviderActions,
            ) => {
              if (error) {
                return <PermissionError />
              }
              return (
                <div>
                  {projectFlags?.length === 0 && (
                    <div>This project has no feature flags to display</div>
                  )}
                  {isLoading && (!projectFlags || !projectFlags.length) && (
                    <div className='centered-container'>
                      <Loader />
                    </div>
                  )}
                  {(!isLoading || (projectFlags && !!projectFlags.length)) && (
                    <div>
                      {(projectFlags && projectFlags.length) ||
                      ((this.state.showArchived ||
                        typeof this.state.search === 'string' ||
                        !!this.state.tags.length) &&
                        !isLoading) ? (
                        <div>
                          <Permission
                            level='environment'
                            permission={Utils.getManageFeaturePermission(
                              Utils.changeRequestsEnabled(
                                environment &&
                                  environment.minimum_change_request_approvals,
                              ),
                            )}
                            id={this.props.environmentId}
                          >
                            {({ permission }) => (
                              <div>
                                <PanelSearch
                                  className='no-pad'
                                  id='features-list'
                                  icon='ion-ios-rocket'
                                  title='Features'
                                  renderSearchWithNoResults
                                  itemHeight={65}
                                  isLoading={FeatureListStore.isLoading}
                                  paging={FeatureListStore.paging}
                                  search={this.state.search}
                                  onChange={(e: InputEvent) => {
                                    this.setState(
                                      { search: Utils.safeParseEventValue(e) },
                                      () => {
                                        AppActions.searchFeatures(
                                          this.props.projectId,
                                          this.props.environmentId,
                                          true,
                                          this.state.search,
                                          this.state.sort,
                                          this.getFilter(),
                                          this.props.pageSize,
                                        )
                                      },
                                    )
                                  }}
                                  nextPage={() =>
                                    AppActions.getFeatures(
                                      this.props.projectId,
                                      this.props.environmentId,
                                      true,
                                      this.state.search,
                                      this.state.sort,
                                      (
                                        FeatureListStore.paging as PagedResponse<ProjectFlag>
                                      ).next || 1,
                                      this.getFilter(),
                                      this.props.pageSize,
                                    )
                                  }
                                  prevPage={() =>
                                    AppActions.getFeatures(
                                      this.props.projectId,
                                      this.props.environmentId,
                                      true,
                                      this.state.search,
                                      this.state.sort,
                                      (
                                        FeatureListStore.paging as PagedResponse<ProjectFlag>
                                      ).previous,
                                      this.getFilter(),
                                      this.props.pageSize,
                                    )
                                  }
                                  goToPage={(page: number) =>
                                    AppActions.getFeatures(
                                      this.props.projectId,
                                      this.props.environmentId,
                                      true,
                                      this.state.search,
                                      this.state.sort,
                                      page,
                                      this.getFilter(),
                                      this.props.pageSize,
                                    )
                                  }
                                  onSortChange={(sort: string) => {
                                    this.setState({ sort }, () => {
                                      AppActions.getFeatures(
                                        this.props.projectId,
                                        this.props.environmentId,
                                        true,
                                        this.state.search,
                                        this.state.sort,
                                        0,
                                        this.getFilter(),
                                        this.props.pageSize,
                                      )
                                    })
                                  }}
                                  sorting={[
                                    {
                                      default: true,
                                      label: 'Name',
                                      order: 'asc',
                                      value: 'name',
                                    },
                                    {
                                      label: 'Created Date',
                                      order: 'asc',
                                      value: 'created_date',
                                    },
                                  ]}
                                  items={projectFlags}
                                  header={
                                    this.props.hideTags ? null : (
                                      <Row className='px-0 pt-0'>
                                        <TagFilter
                                          showUntagged
                                          showClearAll={
                                            (this.state.tags &&
                                              !!this.state.tags.length) ||
                                            this.state.showArchived
                                          }
                                          onClearAll={() =>
                                            this.setState(
                                              { showArchived: false, tags: [] },
                                              this.filter,
                                            )
                                          }
                                          projectId={projectId}
                                          value={this.state.tags}
                                          tagStrategy={this.state.tag_strategy}
                                          onChangeStrategy={(tag_strategy) => {
                                            this.setState(
                                              { tag_strategy },
                                              this.filter,
                                            )
                                          }}
                                          onChange={(tags) => {
                                            FeatureListStore.isLoading = true
                                            if (
                                              tags.includes('') &&
                                              tags.length > 1
                                            ) {
                                              if (
                                                !this.state.tags.includes('')
                                              ) {
                                                this.setState(
                                                  { tags: [''] },
                                                  this.filter,
                                                )
                                              } else {
                                                this.setState(
                                                  {
                                                    tags: tags.filter(
                                                      (v) => !!v,
                                                    ),
                                                  },
                                                  this.filter,
                                                )
                                              }
                                            } else {
                                              this.setState(
                                                { tags },
                                                this.filter,
                                              )
                                            }
                                            AsyncStorage.setItem(
                                              `${projectId}tags`,
                                              JSON.stringify(tags),
                                            )
                                          }}
                                        >
                                          <div className='mr-2'>
                                            <Tag
                                              selected={this.state.showArchived}
                                              onClick={() => {
                                                FeatureListStore.isLoading =
                                                  true
                                                this.setState(
                                                  {
                                                    showArchived:
                                                      !this.state.showArchived,
                                                  },
                                                  this.filter,
                                                )
                                              }}
                                              className='px-2 py-2 ml-2 mr-2'
                                              tag={{
                                                color: '#0AADDF',
                                                label: 'Archived',
                                              }}
                                            />
                                          </div>
                                        </TagFilter>
                                      </Row>
                                    )
                                  }
                                  renderRow={(
                                    projectFlag: ProjectFlag,
                                    i: number,
                                  ) => (
                                    <FeatureRow
                                      hideRemove
                                      hideAudit
                                      hideHistory
                                      widget
                                      readOnly
                                      environmentFlags={environmentFlags}
                                      projectFlags={projectFlags}
                                      permission={permission}
                                      environmentId={environmentId}
                                      projectId={projectId}
                                      index={i}
                                      toggleFlag={toggleFlag}
                                      removeFlag={removeFlag}
                                      projectFlag={projectFlag}
                                    />
                                  )}
                                  filterRow={() => true}
                                />
                              </div>
                            )}
                          </Permission>
                        </div>
                      ) : null}
                    </div>
                  )}
                </div>
              )
            }}
          </FeatureListProvider>
        </div>
      </Provider>
    )
  }
}

export default function Widget() {
  useEffect(() => {
    document.body.classList.add('widget-mode')
  }, [])
  const projectId = useCustomWidgetOptionString(client, 'Project')
  const environmentId = useCustomWidgetOptionString(client, 'Environment')
  const pageSize = useCustomWidgetOptionString(client, 'PageSize') || '5'
  // @ts-ignore context is marked as private but is accessible and needed
  const id = client.context?.widget?.definition?.custom_widget_key
  const isAudit = id === 'flagsmith_audit_widget'
  const hideTags = useCustomWidgetOptionString(client, 'HideTags') === 'Yes'
  const [error, setError] = useState<boolean>(false)
  const [_projectId, setProjectId] = useState<string | null>(projectId || null)
  const [_environmentId, setEnvironmentId] = useState<string | null>(
    environmentId || null,
  )
  const [organisationId, setOrganisationId] = useState<string | null>(null)
  isWidget = true

  useEffect(() => {
    setProjectId(environmentId || null)
  }, [environmentId])

  useEffect(() => {
    setProjectId(projectId || null)
  }, [projectId])

  if (!API.getCookie('t')) {
    resolveAuthFlow({
      isAuthenticated: false,
    })
    return null
  }

  if (error) {
    return <PermissionError />
  }
  if (projectId && environmentId && !error) {
    if (isAudit) {
      return (
        <Provider store={getStore()}>
          <OrganisationWrapper projectId={projectId}>
            <div className='widget-container'>
              <AuditLog
                onErrorChange={setError}
                environmentId={environmentId}
                projectId={projectId}
                pageSize={parseInt(pageSize)}
              />
            </div>
          </OrganisationWrapper>
        </Provider>
      )
    }
    return (
      <OrganisationWrapper projectId={projectId}>
        <FeatureList
          hideTags={hideTags}
          pageSize={parseInt(pageSize)}
          projectId={projectId}
          environmentId={`${environmentId}`}
        />
      </OrganisationWrapper>
    )
  }

  return (
    <OrganisationWrapper projectId={projectId}>
      <div className='text-center pt-5'>
        <h3>Please select the environment you wish to use.</h3>
        <div className='widget-container'>
          <Provider store={getStore()}>
            <OrgEnvironmentSelect
              useApiKey={!isAudit}
              organisationId={organisationId}
              environmentId={_environmentId}
              projectId={_projectId}
              onOrganisationChange={setOrganisationId}
              onProjectChange={setProjectId}
              onEnvironmentChange={setEnvironmentId}
            />
          </Provider>
        </div>
      </div>
    </OrganisationWrapper>
  )
}
