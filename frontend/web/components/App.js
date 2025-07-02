import React, { Component } from 'react'
import { matchPath, withRouter } from 'react-router-dom'
import * as amplitude from '@amplitude/analytics-browser'
import { plugin as engagementPlugin } from '@amplitude/engagement-browser'
import { sessionReplayPlugin } from '@amplitude/plugin-session-replay-browser'
import TwoFactorPrompt from './SimpleTwoFactor/prompt'
import Maintenance from './Maintenance'
import Blocked from './Blocked'
import AppLoader from './AppLoader'
import ButterBar from './ButterBar'
import AccountSettingsPage from './pages/AccountSettingsPage'
import ProjectStore from 'common/stores/project-store'
import { Provider } from 'react-redux'
import { getStore } from 'common/store'
import { resolveAuthFlow } from '@datadog/ui-extensions-sdk'
import ConfigProvider from 'common/providers/ConfigProvider'
import AccountStore from 'common/stores/account-store'
import OrganisationLimit from './OrganisationLimit'
import {
  getStartupErrorText,
  isFlagsmithOnFlagsmithError,
} from './base/errors/init.error'
import OrganisationStore from 'common/stores/organisation-store'
import ScrollToTop from './ScrollToTop'
import AnnouncementPerPage from './AnnouncementPerPage'
import Announcement from './Announcement'
import { getBuildVersion } from 'common/services/useBuildVersion'
import AccountProvider from 'common/providers/AccountProvider'
import Nav from './navigation/Nav'
import 'project/darkMode'
const App = class extends Component {
  static propTypes = {
    children: propTypes.element.isRequired,
  }

  state = {
    asideIsVisible: !isMobile,
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
    const { location } = this.props
    const pathname = location.pathname

    const projectId = this.getProjectId(this.props)
    const environmentId = this.getEnvironmentId(this.props)

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
        {
          buttonText: 'See documentation',
          onClick: () =>
            window.open(
              'https://docs.flagsmith.com/deployment/#running-flagsmith-on-flagsmith',
              '_blank',
            ),
        },
        { size: 'large' },
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

    return (
      <Provider store={getStore()}>
        <AccountProvider
          onNoUser={this.onNoUser}
          onLogout={this.onLogout}
          onLogin={this.onLogin}
        >
          {({ isSaving, user }, { twoFactorLogin }) => {
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
              <Nav
                header={
                  <>
                    <ButterBar
                      projectId={projectId}
                      billingStatus={
                        AccountStore.getOrganisation()?.subscription
                          .billing_status
                      }
                      fofError={this.props.error?.message}
                    />
                    {user && (
                      <>
                        <OrganisationLimit
                          id={AccountStore.getOrganisation()?.id}
                          organisationPlan={
                            AccountStore.getOrganisation()?.subscription.plan
                          }
                        />
                        <div className='container announcement-container'>
                          <div>
                            <Announcement />
                            <AnnouncementPerPage pathname={pathname} />
                          </div>
                        </div>
                      </>
                    )}
                  </>
                }
                activeProject={activeProject}
                projectId={projectId}
                environmentId={environmentId}
              >
                <div>
                  {projectNotLoaded ? (
                    <div className='text-center'>
                      <Loader />
                    </div>
                  ) : (
                    this.props.children
                  )}
                </div>
              </Nav>
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
