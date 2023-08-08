import React, { Component } from 'react'
import propTypes from 'prop-types'
import NavLink from 'react-router-dom/NavLink'
import AsideTitleLink from './AsideTitleLink'
import Collapsible from './Collapsible'
import OrgSettingsIcon from './svg/OrgSettingsIcon'
import EnvironmentDropdown from './EnvironmentDropdown'
import ProjectStore from 'common/stores/project-store'
import ChangeRequestStore from 'common/stores/change-requests-store'
import getBuildVersion from 'project/getBuildVersion'
import ConfigProvider from 'common/providers/ConfigProvider'
import Permission from 'common/providers/Permission'
import Icon from './Icon'

const Aside = class extends Component {
  static displayName = 'Aside'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  static propTypes = {
    asideIsVisible: propTypes.bool,
    className: propTypes.string,
    toggleAside: propTypes.func,
  }

  constructor(props, context) {
    super(props, context)
    this.state = { isOpenProject: true }
    ES6Component(this)
    AppActions.getProject(this.props.projectId)
    if (this.props.environmentId && this.props.environmentId !== 'create') {
      AppActions.getChangeRequests(this.props.environmentId, {})
    }
    this.listenTo(ChangeRequestStore, 'change', () => this.forceUpdate())
    this.listenTo(ProjectStore, 'loaded', () => {
      const environment = ProjectStore.getEnvironment(this.props.environmentId)
      if (environment) {
        AppActions.getChangeRequests(
          this.props.environmentId,
          Utils.changeRequestsEnabled(
            environment.minimum_change_request_approvals,
          )
            ? {}
            : { live_from_after: new Date().toISOString() },
        )
      }
    })
  }

  componentDidMount() {
    getBuildVersion().then((version) => {
      this.setState({ version })
    })
  }

  componentDidUpdate(prevProps) {
    const environment = ProjectStore.getEnvironment(this.props.environmentId)
    if (this.props.projectId !== prevProps.projectId) {
      AppActions.getProject(prevProps.projectId)
    }
    if (this.props.environmentId !== prevProps.environmentId) {
      if (environment) {
        AppActions.getChangeRequests(
          this.props.environmentId,
          Utils.changeRequestsEnabled(
            environment.minimum_change_request_approvals,
          )
            ? {}
            : { live_from_after: new Date().toISOString() },
        )
      }
    }
  }

  onProjectSave = () => {
    AppActions.refreshOrganisation()
  }

  render() {
    const { asideIsVisible, toggleAside } = this.props
    let integrations = Utils.getFlagsmithValue('integrations') || '[]'
    integrations = JSON.parse(integrations)
    const environmentId =
      (this.props.environmentId !== 'create' && this.props.environmentId) ||
      (ProjectStore.model &&
        ProjectStore.model.environments[0] &&
        ProjectStore.model.environments[0].api_key)
    const environment = ProjectStore.getEnvironment(this.props.environmentId)
    const hasRbacPermission = Utils.getPlansPermission('AUDIT')
    const changeRequest =
      environment &&
      Utils.changeRequestsEnabled(environment.minimum_change_request_approvals)
        ? ChangeRequestStore.model[this.props.environmentId]
        : null
    const changeRequests = changeRequest?.count || 0
    const scheduled =
      (environment &&
        ChangeRequestStore.scheduled[this.props.environmentId]?.count) ||
      0
    return (
      <OrganisationProvider>
        {() => (
          <ProjectProvider
            id={this.props.projectId}
            onSave={this.onProjectSave}
          >
            {({ project }) => (
              <React.Fragment>
                <div
                  className={`aside ${this.props.className || ''}`}
                  style={
                    !asideIsVisible
                      ? {
                          overflow: 'hidden',
                          width: 0,
                        }
                      : isMobile
                      ? {}
                      : {}
                  }
                >
                  {isMobile && (
                    <div
                      role='button'
                      className='clickable toggle'
                      onClick={toggleAside}
                    >
                      {!asideIsVisible ? (
                        <span className='icon ion-md-menu' />
                      ) : (
                        <span className='icon ion-md-close' />
                      )}
                    </div>
                  )}
                  <div className='row ml-0 mr-0 aside__wrapper'>
                    {
                      <React.Fragment>
                        <div className='aside__main-content px-0'>
                          <a href={'/projects'} className='nav-logo'>
                            <Icon name='nav-logo' />
                          </a>
                          <hr className='my-0 py-0' />
                          <Collapsible
                            title={
                              project && project.name ? (
                                <Row>
                                  {project.name}{' '}
                                  {Utils.getFlagsmithHasFeature(
                                    'edge_identities',
                                  ) && (
                                    <div className='text-center'>
                                      <span
                                        style={{
                                          border: 'none',
                                          bottom: 2,
                                          left: 5,
                                          position: 'relative',
                                        }}
                                        className='chip chip--active bg-secondary'
                                      >
                                        <a
                                          data-test={
                                            Utils.getIsEdge()
                                              ? 'edge-project'
                                              : 'core-project'
                                          }
                                          href='https://docs.flagsmith.com/advanced-use/edge-api#enabling-the-edge-api'
                                          className='text-white font-weight-bold'
                                        >
                                          {Utils.getIsEdge() ? (
                                            'Edge'
                                          ) : Utils.isMigrating() ? (
                                            <Tooltip title='Migrating to Edge'>
                                              Depending on the amount of project
                                              data, migrating can take a while.
                                              Refresh the page to track
                                              progress.
                                            </Tooltip>
                                          ) : (
                                            'Core'
                                          )}
                                        </a>
                                      </span>
                                    </div>
                                  )}
                                </Row>
                              ) : (
                                'No Project'
                              )
                            }
                            onClick={() => {
                              this.setState((prev) => {
                                return {
                                  isOpenProject: !prev.isOpenProject,
                                }
                              })
                            }}
                            active={this.state.isOpenProject}
                            className='collapsible-project'
                          >
                            <Permission
                              level='project'
                              permission='ADMIN'
                              id={this.props.projectId}
                            >
                              {({ permission }) =>
                                permission && (
                                  <NavLink
                                    id='project-settings-link'
                                    activeClassName='active'
                                    className='aside__nav-item mx-3'
                                    to={`/project/${this.props.projectId}/settings`}
                                  >
                                    <span className='mr-2'>
                                      <Icon name='options-2' />
                                    </span>
                                    Project Settings
                                  </NavLink>
                                )
                              }
                            </Permission>

                            <NavLink
                              to={`/project/${project.id}/environment/${environmentId}/segments`}
                              id='segments-link'
                              className='aside__nav-item mx-3'
                            >
                              <span className='mr-2'>
                                <Icon name='pie-chart' />
                              </span>
                              Segments
                            </NavLink>
                            <NavLink
                              id='integrations-link'
                              activeClassName='active'
                              className='aside__nav-item mx-3'
                              to={`/project/${project.id}/environment/${environmentId}/compare`}
                              exact
                            >
                              <span className='mr-2'>
                                <Icon name='bar-chart' />
                              </span>
                              Compare
                            </NavLink>

                            <Permission
                              level='project'
                              permission='VIEW_AUDIT_LOG'
                              id={this.props.projectId}
                            >
                              {({ permission }) =>
                                permission &&
                                hasRbacPermission && (
                                  <NavLink
                                    id='audit-log-link'
                                    activeClassName='active'
                                    className='aside__nav-item mx-3'
                                    to={`/project/${this.props.projectId}/environment/${environmentId}/audit-log`}
                                  >
                                    <span className='mr-2'>
                                      <Icon name='list' />
                                    </span>
                                    Audit Log
                                  </NavLink>
                                )
                              }
                            </Permission>

                            {!hasRbacPermission && (
                              <Tooltip
                                title={
                                  <a
                                    href='#'
                                    className='aside__nav-item disabled mx-3'
                                  >
                                    <span className='mr-2'>
                                      <Icon name='list' />
                                    </span>
                                    Audit Log
                                  </a>
                                }
                              >
                                This feature is available with our scaleup plan
                              </Tooltip>
                            )}
                            {!!integrations.length && (
                              <Permission
                                level='project'
                                permission='CREATE_ENVIRONMENT'
                                id={this.props.projectId}
                              >
                                {({ permission }) =>
                                  permission && (
                                    <NavLink
                                      id='integrations-link'
                                      activeClassName='active'
                                      className='aside__nav-item mx-3'
                                      to={`/project/${this.props.projectId}/integrations`}
                                      exact
                                    >
                                      <span className='mr-2'>
                                        <Icon name='layers' />
                                      </span>
                                      Integrations
                                    </NavLink>
                                  )
                                }
                              </Permission>
                            )}
                          </Collapsible>
                          <hr className='my-0 py-0' />
                          <Permission
                            level='project'
                            permission='CREATE_ENVIRONMENT'
                            id={this.props.projectId}
                          >
                            {({ permission }) =>
                              permission && (
                                <NavLink
                                  id='create-env-link'
                                  className='aside__header-link mt-2'
                                  to={`/project/${this.props.projectId}/environment/create`}
                                  exact
                                >
                                  <AsideTitleLink
                                    tooltip='Create Environment'
                                    className='mt-4'
                                    title='Create Environment'
                                  />
                                </NavLink>
                              )
                            }
                          </Permission>

                          {
                            <div className='aside__environments-wrapper'>
                              <EnvironmentDropdown
                                renderRow={(environment, onClick) => (
                                  <Collapsible
                                    data-test={`switch-environment-${environment.name.toLowerCase()}${
                                      environmentId === `${environment.api_key}`
                                        ? '-active'
                                        : ''
                                    }`}
                                    onClick={onClick}
                                    active={
                                      environment.api_key === environmentId
                                    }
                                    title={environment.name}
                                  >
                                    <Permission
                                      level='environment'
                                      permission={Utils.getViewIdentitiesPermission()}
                                      id={environment.api_key}
                                    >
                                      {({
                                        isLoading: manageIdentityLoading,
                                        permission: manageIdentityPermission,
                                      }) => (
                                        <Permission
                                          level='environment'
                                          permission='ADMIN'
                                          id={environment.api_key}
                                        >
                                          {({
                                            isLoading,
                                            permission: environmentAdmin,
                                          }) =>
                                            isLoading ||
                                            manageIdentityLoading ? (
                                              <div className='text-center'>
                                                <Loader />
                                              </div>
                                            ) : (
                                              <div className='aside__environment-nav list-unstyled mb-0'>
                                                <NavLink
                                                  className='aside__environment-list-item'
                                                  id='features-link'
                                                  to={`/project/${project.id}/environment/${environment.api_key}/features`}
                                                >
                                                  Features
                                                </NavLink>
                                                <NavLink
                                                  activeClassName='active'
                                                  className='aside__environment-list-item mt-1'
                                                  id='change-requests-link'
                                                  to={`/project/${project.id}/environment/${environment.api_key}/scheduled-changes/`}
                                                >
                                                  Scheduling
                                                  {scheduled ? (
                                                    <span className='ml-1 unread'>
                                                      {scheduled}
                                                    </span>
                                                  ) : null}
                                                </NavLink>
                                                <NavLink
                                                  activeClassName='active'
                                                  className='aside__environment-list-item mt-1'
                                                  id='change-requests-link'
                                                  to={`/project/${project.id}/environment/${environment.api_key}/change-requests/`}
                                                >
                                                  Change Requests{' '}
                                                  {changeRequests ? (
                                                    <span className='unread'>
                                                      {changeRequests}
                                                    </span>
                                                  ) : null}
                                                </NavLink>
                                                {manageIdentityPermission && (
                                                  <NavLink
                                                    id='users-link'
                                                    className='aside__environment-list-item mt-1'
                                                    exact
                                                    to={`/project/${project.id}/environment/${environment.api_key}/users`}
                                                  >
                                                    Identities
                                                  </NavLink>
                                                )}

                                                {environmentAdmin && (
                                                  <NavLink
                                                    id='env-settings-link'
                                                    className='aside__environment-list-item mt-1'
                                                    to={`/project/${project.id}/environment/${environment.api_key}/settings`}
                                                  >
                                                    Settings
                                                  </NavLink>
                                                )}
                                              </div>
                                            )
                                          }
                                        </Permission>
                                      )}
                                    </Permission>
                                  </Collapsible>
                                )}
                                projectId={this.props.projectId}
                                environmentId={environmentId}
                                clearableValue={false}
                                onChange={(environment) => {
                                  this.context.router.history.push(
                                    `/project/${this.props.projectId}/environment/${environment}/features`,
                                  )
                                  AsyncStorage.setItem(
                                    'lastEnv',
                                    JSON.stringify({
                                      environmentId: environment,
                                      orgId: AccountStore.getOrganisation().id,
                                      projectId: this.props.projectId,
                                    }),
                                  )
                                }}
                              />
                            </div>
                          }

                          <div className='flex flex-1' />

                          <div className='align-self-end'>
                            {Utils.getFlagsmithHasFeature('demo_feature') && (
                              <a
                                style={{
                                  color:
                                    Utils.getFlagsmithValue('demo_feature') ||
                                    '#43424f',
                                }}
                                className='aside__nav-item'
                                href='https://docs.flagsmith.com'
                              >
                                <i className='icon mr-2 ion-ios-star aside__nav-item--icon' />
                                Super cool demo feature!
                              </a>
                            )}

                            {Utils.getFlagsmithHasFeature('broken_feature') && (
                              <Link to='/broken' className='aside__nav-item'>
                                <i className='icon mr-2 ion-ios-warning aside__nav-item--icon' />
                                Demo Broken Feature
                              </Link>
                            )}
                            {this.state.version && (
                              <div className='px-4 fs-small lh-sm text-white my-3'>
                                {this.state.version.tag !== 'Unknown' && (
                                  <Tooltip
                                    html
                                    title={
                                      <span>
                                        <span className='ml-2 icon ion-ios-pricetag' />{' '}
                                        {this.state.version.tag}
                                      </span>
                                    }
                                  >
                                    {`${
                                      this.state.version.frontend_sha !==
                                      'Unknown'
                                        ? `Frontend SHA: ${this.state.version.frontend_sha}`
                                        : ''
                                    }${
                                      this.state.version.backend_sha !==
                                      'Unknown'
                                        ? `${
                                            this.state.version.frontend_sha !==
                                            'Unknown'
                                              ? '<br/>'
                                              : ''
                                          }Backend SHA: ${
                                            this.state.version.backend_sha
                                          }`
                                        : ''
                                    }`}
                                  </Tooltip>
                                )}
                              </div>
                            )}

                            {E2E &&
                              AccountStore.getOrganisationRole() ===
                                'ADMIN' && (
                                <NavLink
                                  id='organisation-settings-link'
                                  activeClassName='active'
                                  className='aside__nav-item'
                                  to={`/project/${this.props.projectId}/environment/${environmentId}/organisation-settings`}
                                >
                                  <OrgSettingsIcon className='aside__nav-item--icon' />
                                  Organisation
                                </NavLink>
                              )}
                          </div>
                        </div>
                      </React.Fragment>
                    }
                  </div>
                </div>
              </React.Fragment>
            )}
          </ProjectProvider>
        )}
      </OrganisationProvider>
    )
  }
}

module.exports = ConfigProvider(Aside)
