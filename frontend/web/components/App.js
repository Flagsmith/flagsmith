import React, { Component, Fragment } from 'react'
import { Link, withRouter, matchPath } from 'react-router-dom'
import * as amplitude from '@amplitude/analytics-browser'
import { plugin as engagementPlugin } from '@amplitude/engagement-browser'
import { sessionReplayPlugin } from '@amplitude/plugin-session-replay-browser'
import NavLink from 'react-router-dom/NavLink'
import TwoFactorPrompt from './SimpleTwoFactor/prompt'
import Maintenance from './Maintenance'
import Blocked from './Blocked'
import AppLoader from './AppLoader'
import ButterBar from './ButterBar'
import AccountSettingsPage from './pages/AccountSettingsPage'
import Headway from './Headway'
import ProjectStore from 'common/stores/project-store'
import { Provider } from 'react-redux'
import { getStore } from 'common/store'
import { resolveAuthFlow } from '@datadog/ui-extensions-sdk'
import ConfigProvider from 'common/providers/ConfigProvider'
import Icon from './Icon'
import AccountStore from 'common/stores/account-store'
import OrganisationLimit from './OrganisationLimit'
import GithubStar from './GithubStar'
import classNames from 'classnames'
import { apps, gitBranch, gitCompare, statsChart } from 'ionicons/icons'
import {
  getStartupErrorText,
  isFlagsmithOnFlagsmithError,
  isMaintenanceError,
} from './base/errors/init.error'
import NavSubLink from './navigation/NavSubLink'
import SettingsIcon from './svg/SettingsIcon'
import UsersIcon from './svg/UsersIcon'
import BreadcrumbSeparator from './BreadcrumbSeparator'
import OrganisationStore from 'common/stores/organisation-store'
import SegmentsIcon from './svg/SegmentsIcon'
import AuditLogIcon from './svg/AuditLogIcon'
import Permission from 'common/providers/Permission'
import HomeAside from './pages/HomeAside'
import ScrollToTop from './ScrollToTop'
import AnnouncementPerPage from './AnnouncementPerPage'
import Announcement from './Announcement'
import { getBuildVersion } from 'common/services/useBuildVersion'

const App = class extends Component {
  static propTypes = {
    children: propTypes.element.isRequired,
  }

  state = {
    asideIsVisible: !isMobile,
    lastEnvironmentId: '',
    lastProjectId: '',
    pin: '',
    showAnnouncement: true,
  }

  constructor(props, context) {
    super(props, context)
    ES6Component(this)
  }

  getProjectId = (props) => {
    const { location } = props
    const pathname = location.pathname

    const match = matchPath(pathname, {
      exact: false,
      path: '/project/:projectId/environment/:environmentId',
      strict: false,
    })
    const match2 = matchPath(pathname, {
      exact: false,
      path: '/project/:projectId',
      strict: false,
    })
    const projectId =
      _.get(match, 'params.projectId') || _.get(match2, 'params.projectId')
    return !!projectId && parseInt(projectId)
  }
  getEnvironmentId = (props) => {
    const { location } = props
    const pathname = location.pathname

    const match = matchPath(pathname, {
      exact: false,
      path: '/project/:projectId/environment/:environmentId',
      strict: false,
    })

    const environmentId = _.get(match, 'params.environmentId')
    return environmentId
  }

  componentDidMount = () => {
    if (Project.amplitude) {
      amplitude.init(Project.amplitude, {
        defaultTracking: true,
        serverZone: 'EU',
      })
      amplitude.add(engagementPlugin())
      const sessionReplayTracking = sessionReplayPlugin({
        sampleRate: 0.5,
        serverZone: 'EU',
      })
      amplitude.add(sessionReplayTracking)
    }
    getBuildVersion(getStore(), {})
    this.state.projectId = this.getProjectId(this.props)
    if (this.state.projectId) {
      AppActions.getProject(this.state.projectId)
    }
    this.listenTo(OrganisationStore, 'change', () => this.forceUpdate())
    this.listenTo(ProjectStore, 'change', () => this.forceUpdate())
    if (AccountStore.model) {
      this.onLogin()
    }
    window.addEventListener('scroll', this.handleScroll)
    const updateLastViewed = () => {
      AsyncStorage.getItem('lastEnv').then((res) => {
        if (res) {
          const lastEnv = JSON.parse(res)
          this.setState({
            lastEnvironmentId: lastEnv.environmentId,
            lastProjectId: lastEnv.projectId,
          })
        }
      })
    }
    this.props.history.listen(updateLastViewed)
    updateLastViewed()
  }

  componentDidUpdate(prevProps) {
    if (prevProps.location.pathname !== this.props.location.pathname) {
      const newProjectId = this.getProjectId(this.props)
      if (this.state.projectId !== newProjectId && !!newProjectId) {
        this.state.projectId = newProjectId
        AppActions.getProject(this.state.projectId)
      }

      if (isMobile) {
        this.setState({ asideIsVisible: false })
      }
      this.hideMobileNav()
      AsyncStorage.getItem('lastEnv').then((res) => {
        if (res) {
          const { environmentId, projectId } = JSON.parse(res)
          this.setState({
            lastEnvironmentId: environmentId,
            lastProjectId: projectId,
          })
        }
      })
    }
  }

  hideMobileNav = () => {
    if (this.mobileNav && this.mobileNav.isActive()) {
      this.mobileNav.toggle()
    }
  }

  toggleAside = () => {
    this.setState({ asideIsVisible: !this.state.asideIsVisible })
  }

  onLogin = () => {
    resolveAuthFlow({
      isAuthenticated: true,
    })

    let redirect = API.getRedirect()
    const invite = API.getInvite()
    if (invite) {
      redirect = `/invite/${invite}`
    }

    const referrer = API.getReferrer()
    let query = ''
    if (referrer) {
      query = `?${Utils.toParam(referrer)}`
    }

    if (AccountStore.ephemeral_token) {
      this.forceUpdate()
      return
    }

    if (!AccountStore.getOrganisation() && !invite) {
      // If user has no organisation redirect to /create
      this.props.history.replace(`/create${query}`)
      return
    }

    // Redirect on login
    if (
      this.props.location.pathname === '/' ||
      this.props.location.pathname === '/widget' ||
      this.props.location.pathname === '/saml' ||
      this.props.location.pathname.includes('/oauth') ||
      this.props.location.pathname === '/login' ||
      this.props.location.pathname === '/signup'
    ) {
      if (redirect) {
        API.setRedirect('')
        this.props.history.replace(redirect)
      } else {
        AsyncStorage.getItem('lastEnv').then((res) => {
          if (this.props.location.search.includes('github-redirect')) {
            this.props.history.replace(
              `/github-setup${this.props.location.search}`,
            )
            return
          }
          if (res) {
            const lastEnv = JSON.parse(res)
            const lastOrg = _.find(AccountStore.getUser().organisations, {
              id: lastEnv.orgId,
            })
            if (!lastOrg) {
              this.props.history.replace('/organisations')
              return
            }

            const org = AccountStore.getOrganisation()
            if (
              !org ||
              (org.id !== lastOrg.id && this.getEnvironmentId(this.props))
            ) {
              AppActions.selectOrganisation(lastOrg.id)
              AppActions.getOrganisation(lastOrg.id)
            }

            this.props.history.replace(
              `/project/${lastEnv.projectId}/environment/${lastEnv.environmentId}/features`,
            )
            return
          }

          if (
            Utils.getFlagsmithHasFeature('welcome_page') &&
            AccountStore.getUser()?.isGettingStarted
          ) {
            this.props.history.replace('/getting-started')
          } else {
            this.props.history.replace(Utils.getOrganisationHomePage())
          }
        })
      }
    }

    if (Utils.getFlagsmithHasFeature('dark_mode')) {
      document.body.classList.add('dark')
    }
  }

  handleScroll = () => {
    if (this.scrollPos < 768 && $(document).scrollTop() >= 768) {
      this.setState({ myClassName: 'scrolled' })
    } else if (this.scrollPos >= 768 && $(document).scrollTop() < 768) {
      this.setState({ myClassName: '' })
    }
    this.scrollPos = $(document).scrollTop()
  }

  onLogout = () => {
    resolveAuthFlow({
      isAuthenticated: false,
    })
    if (document.location.href.includes('saml?')) {
      return
    }
    this.props.history.replace('/')
  }

  closeAnnouncement = (announcementId) => {
    this.setState({ showAnnouncement: false })
    flagsmith.setTrait(`dismissed_announcement`, announcementId)
  }

  render() {
    if (
      Utils.getFlagsmithHasFeature('dark_mode') &&
      !document.body.classList.contains('dark')
    ) {
      document.body.classList.add('dark')
    }
    const { location } = this.props
    const pathname = location.pathname
    const { asideIsVisible, lastEnvironmentId, lastProjectId } = this.state
    const projectId = this.getProjectId(this.props)
    const environmentId = this.getEnvironmentId(this.props)
    const isCreateEnvironment = environmentId === 'create'
    const isCreateOrganisation = document.location.pathname === '/create'
    const storageHasParams = lastEnvironmentId || lastProjectId
    const pageHasAside = environmentId || projectId || storageHasParams
    const isHomepage =
      pathname === '/' ||
      pathname === '/login' ||
      pathname === '/signup' ||
      pathname === '/github-setup' ||
      pathname.includes('/invite')
    if (
      AccountStore.getOrganisation() &&
      AccountStore.getOrganisation().block_access_to_admin &&
      pathname !== '/organisations'
    ) {
      return <Blocked />
    }
    const maintenanceMode =
      Utils.getFlagsmithHasFeature('maintenance_mode') || Project.maintenance
    const isUnknownError =
      this.props.error && !isFlagsmithOnFlagsmithError(this.props.error)
    if (maintenanceMode || !window.projectOverrides || isUnknownError) {
      return <Maintenance />
    }

    if (this.props.error && isFlagsmithOnFlagsmithError(this.props.error)) {
      toast(
        getStartupErrorText(this.props.error),
        'danger',
        2 * 60 * 1000,
        undefined,
        'top',
      )
    }

    const activeProject = OrganisationStore.getProject(projectId)
    const projectNotLoaded =
      !activeProject && document.location.href.includes('project/')

    if (this.props.isLoading) {
      return (
        <AccountProvider
          onNoUser={this.onNoUser}
          onLogout={this.onLogout}
          onLogin={this.onLogin}
        >
          {() => (
            <div id='login-page'>
              <AppLoader />
            </div>
          )}
        </AccountProvider>
      )
    }

    if (AccountStore.forced2Factor()) {
      return <AccountSettingsPage isLoginPage={true} />
    }

    if (document.location.pathname.includes('widget')) {
      return <div>{this.props.children}</div>
    }
    const isOrganisationSelect = document.location.pathname === '/organisations'
    const integrations = Object.keys(Utils.getIntegrationData())
    const projectMetricsTooltipEnabled = Utils.getFlagsmithHasFeature(
      'project_metrics_tooltip',
    )

    return (
      <Provider store={getStore()}>
        <AccountProvider
          onNoUser={this.onNoUser}
          onLogout={this.onLogout}
          onLogin={this.onLogin}
        >
          {({ isSaving, user }, { twoFactorLogin }) => {
            const inner = (
              <div>
                <ButterBar
                  projectId={projectId}
                  billingStatus={
                    AccountStore.getOrganisation()?.subscription.billing_status
                  }
                />
                {projectNotLoaded ? (
                  <div className='text-center'>
                    <Loader />
                  </div>
                ) : (
                  <Fragment>
                    {user && (
                      <OrganisationLimit
                        id={AccountStore.getOrganisation()?.id}
                        organisationPlan={
                          AccountStore.getOrganisation()?.subscription.plan
                        }
                      />
                    )}
                    {user && (
                      <div className='container announcement-container mt-4'>
                        <div>
                          <Announcement />
                          <AnnouncementPerPage pathname={pathname} />
                        </div>
                      </div>
                    )}

                    {this.props.children}
                  </Fragment>
                )}
              </div>
            )
            return user && user.twoFactorPrompt ? (
              <div className='col-md-6 push-md-3 mt-5'>
                <TwoFactorPrompt
                  pin={this.state.pin}
                  error={this.state.error}
                  onSubmit={() => {
                    this.setState({ error: false })
                    twoFactorLogin(this.state.pin, () => {
                      this.setState({ error: true })
                    })
                  }}
                  isLoading={isSaving}
                  onChange={(e) =>
                    this.setState({ pin: Utils.safeParseEventValue(e) })
                  }
                />
              </div>
            ) : (
              <div className='fs-small'>
                <div>
                  {!isHomepage &&
                    (!pageHasAside || !asideIsVisible || !isMobile) && (
                      <div className='d-flex py-0'>
                        <Flex className='flex-row px-3 bg-faint'>
                          {user ? (
                            <React.Fragment>
                              <nav className='mt-2 mb-1 space flex-row hidden-xs-down'>
                                <Row className='gap-2'>
                                  <Link
                                    data-test='home-link'
                                    to={'/organisations'}
                                  >
                                    <img
                                      style={{
                                        height: 24,
                                        width: 24,
                                      }}
                                      src='/static/images/nav-logo.png'
                                    />
                                  </Link>
                                  {!(
                                    isOrganisationSelect || isCreateOrganisation
                                  ) && (
                                    <div className='d-flex gap-1 ml-1 align-items-center'>
                                      <BreadcrumbSeparator
                                        projectId={projectId}
                                        hideSlash={!activeProject}
                                        focus='organisation'
                                      >
                                        <NavLink
                                          id='organisation-link'
                                          data-test='organisation-link'
                                          activeClassName='active'
                                          className={classNames(
                                            'breadcrumb-link',
                                            {
                                              active: !projectId,
                                            },
                                          )}
                                          to={Utils.getOrganisationHomePage()}
                                        >
                                          <div>
                                            {
                                              AccountStore.getOrganisation()
                                                ?.name
                                            }
                                          </div>
                                        </NavLink>
                                      </BreadcrumbSeparator>
                                      {!!activeProject && (
                                        <BreadcrumbSeparator
                                          projectId={projectId}
                                          hideSlash
                                          focus='project'
                                        >
                                          <NavLink
                                            to={`/project/${activeProject.id}`}
                                            id='project-link'
                                            activeClassName='active'
                                            className={'breadcrumb-link active'}
                                          >
                                            <div>{activeProject.name}</div>
                                          </NavLink>
                                        </BreadcrumbSeparator>
                                      )}
                                    </div>
                                  )}
                                </Row>
                                <Row className='gap-3'>
                                  {Utils.getFlagsmithHasFeature(
                                    'welcome_page',
                                  ) && (
                                    <NavLink
                                      activeClassName='active'
                                      to={'/getting-started'}
                                      className='d-flex lh-1 align-items-center'
                                    >
                                      <span className='mr-1'>
                                        <Icon
                                          name='rocket'
                                          width={20}
                                          fill='#9DA4AE'
                                        />
                                      </span>
                                      Getting Started
                                    </NavLink>
                                  )}

                                  <a
                                    className='d-flex lh-1 align-items-center'
                                    href={'https://docs.flagsmith.com'}
                                  >
                                    <span className='mr-1'>
                                      <Icon
                                        name='file-text'
                                        width={20}
                                        fill='#9DA4AE'
                                      />
                                    </span>
                                    Docs
                                  </a>
                                  <NavLink
                                    className='d-flex lh-1 align-items-center'
                                    id='account-settings-link'
                                    data-test='account-settings-link'
                                    activeClassName='active'
                                    to={'/account'}
                                  >
                                    <span className='mr-1'>
                                      <Icon
                                        name='person'
                                        width={20}
                                        fill='#9DA4AE'
                                      />
                                    </span>
                                    Account
                                  </NavLink>
                                  <GithubStar />

                                  <Headway className='cursor-pointer' />
                                </Row>
                              </nav>
                            </React.Fragment>
                          ) : (
                            <div />
                          )}
                        </Flex>
                      </div>
                    )}
                  {!isOrganisationSelect && !isCreateOrganisation && (
                    <div className='py-0 bg-faint gap-4 d-flex px-3'>
                      {activeProject ? (
                        <>
                          <NavSubLink
                            icon={gitBranch}
                            className={environmentId ? 'active' : ''}
                            id={`features-link`}
                            to={`/project/${projectId}/environment/${
                              lastEnvironmentId || environmentId
                            }/features`}
                          >
                            Environments
                          </NavSubLink>
                          <NavSubLink
                            icon={<SegmentsIcon />}
                            id={`segments-link`}
                            to={`/project/${projectId}/segments`}
                          >
                            Segments
                          </NavSubLink>
                          <Permission
                            level='project'
                            permission='VIEW_AUDIT_LOG'
                            id={projectId}
                          >
                            {({ permission }) =>
                              permission && (
                                <NavSubLink
                                  icon={<AuditLogIcon />}
                                  id='audit-log-link'
                                  to={`/project/${projectId}/audit-log`}
                                  data-test='audit-log-link'
                                >
                                  Audit Log
                                </NavSubLink>
                              )
                            }
                          </Permission>
                          {!!integrations.length && (
                            <NavSubLink
                              icon={<Icon name='layers' />}
                              id='integrations-link'
                              to={`/project/${projectId}/integrations`}
                            >
                              Integrations
                            </NavSubLink>
                          )}
                          <NavSubLink
                            icon={gitCompare}
                            id='compare-link'
                            to={`/project/${projectId}/compare`}
                          >
                            Compare
                          </NavSubLink>
                          {projectMetricsTooltipEnabled && (
                            <NavSubLink
                              icon={gitCompare}
                              to=''
                              id='reporting-link'
                              disabled
                              tooltip={
                                Utils.getFlagsmithValue(
                                  'project_metrics_tooltip',
                                ) || 'Coming soon - fallback'
                              }
                            >
                              Reporting
                            </NavSubLink>
                          )}
                          <Permission
                            level='project'
                            permission='ADMIN'
                            id={projectId}
                          >
                            {({ permission }) =>
                              permission && (
                                <NavSubLink
                                  icon={<SettingsIcon />}
                                  id='project-settings-link'
                                  to={`/project/${projectId}/settings`}
                                >
                                  Project Settings
                                </NavSubLink>
                              )
                            }
                          </Permission>
                          {Utils.getFlagsmithHasFeature(
                            'release_pipelines',
                          ) && (
                            <Permission
                              level='project'
                              permission='ADMIN'
                              id={projectId}
                            >
                              {({ permission }) =>
                                permission && (
                                  <NavSubLink
                                    icon={<Icon name='flash' />}
                                    id='release-pipelines-link'
                                    to={`/project/${projectId}/release-pipelines`}
                                  >
                                    Release Pipelines
                                  </NavSubLink>
                                )
                              }
                            </Permission>
                          )}
                        </>
                      ) : (
                        !!AccountStore.getOrganisation() && (
                          <>
                            <NavSubLink
                              icon={apps}
                              id='projects-link'
                              to={Utils.getOrganisationHomePage()}
                            >
                              Projects
                            </NavSubLink>
                            <NavSubLink
                              data-test='users-and-permissions'
                              icon={<UsersIcon />}
                              id='permissions-link'
                              to={`/organisation/${
                                AccountStore.getOrganisation().id
                              }/permissions`}
                            >
                              Users and Permissions
                            </NavSubLink>
                            {!Project.disableAnalytics &&
                              AccountStore.isAdmin() && (
                                <NavSubLink
                                  icon={statsChart}
                                  id='permissions-link'
                                  to={`/organisation/${
                                    AccountStore.getOrganisation().id
                                  }/usage`}
                                >
                                  Usage
                                </NavSubLink>
                              )}
                            {AccountStore.isAdmin() && (
                              <>
                                {Utils.getFlagsmithHasFeature(
                                  'organisation_integrations',
                                ) && (
                                  <NavSubLink
                                    icon={<Icon name='layers' />}
                                    id='integrations-link'
                                    to={`/organisation/${
                                      AccountStore.getOrganisation().id
                                    }/integrations`}
                                  >
                                    Organisation Integrations
                                  </NavSubLink>
                                )}
                                <NavSubLink
                                  icon={<SettingsIcon />}
                                  id='org-settings-link'
                                  data-test='org-settings-link'
                                  to={`/organisation/${
                                    AccountStore.getOrganisation().id
                                  }/settings`}
                                >
                                  Organisation Settings
                                </NavSubLink>
                              </>
                            )}
                          </>
                        )
                      )}
                    </div>
                  )}
                  <hr className='my-0 py-0' />
                  {/*{!isHomepage && (*/}
                  {/*  <Aside*/}
                  {/*    projectId={projectId || lastProjectId}*/}
                  {/*    environmentId={environmentId || lastEnvironmentId}*/}
                  {/*    toggleAside={this.toggleAside}*/}
                  {/*    asideIsVisible={asideIsVisible}*/}
                  {/*    disabled={!pageHasAside}*/}
                  {/*  />*/}
                  {/*)}*/}
                  {environmentId && !isCreateEnvironment ? (
                    <div className='d-flex'>
                      <HomeAside
                        history={this.props.history}
                        environmentId={environmentId}
                        projectId={projectId}
                      />
                      <div className='aside-container'>{inner}</div>
                    </div>
                  ) : (
                    inner
                  )}
                </div>
              </div>
            )
          }}
        </AccountProvider>
        <ScrollToTop />
      </Provider>
    )
  }
}

App.propTypes = {
  history: RequiredObject,
  location: RequiredObject,
  match: RequiredObject,
}

export default withRouter(ConfigProvider(App))

if (E2E) {
  const e2e = document.getElementsByClassName('e2e')
  if (e2e && e2e[0]) {
    e2e[0].classList.toggle('display-none')
  }
}
