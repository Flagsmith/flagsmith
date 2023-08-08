import React, { Component } from 'react'
import { matchPath } from 'react-router'
import { withRouter } from 'react-router-dom'
import amplitude from 'amplitude-js'
import NavLink from 'react-router-dom/NavLink'
import Aside from './Aside'
import TwoFactorPrompt from './SimpleTwoFactor/prompt'
import Maintenance from './Maintenance'
import Blocked from './Blocked'
import AppLoader from './AppLoader'
import ButterBar from './ButterBar'
import AccountSettingsPage from './pages/AccountSettingsPage'
import Headway from './Headway'
import ProjectStore from 'common/stores/project-store'
import getBuildVersion from 'project/getBuildVersion'
import { Provider } from 'react-redux'
import { getStore } from 'common/store'
import { resolveAuthFlow } from '@datadog/ui-extensions-sdk'
import ConfigProvider from 'common/providers/ConfigProvider'
import Permission from 'common/providers/Permission'
import { getOrganisationUsage } from 'common/services/useOrganisationUsage'
import Button from './base/forms/Button'
import Icon from 'components/Icon'

const App = class extends Component {
  static propTypes = {
    children: propTypes.element.isRequired,
  }

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  state = {
    asideIsVisible: !isMobile,
    pin: '',
    totalApiCalls: 0,
  }

  constructor(props, context) {
    super(props, context)
    ES6Component(this)
  }

  componentDidMount = () => {
    getBuildVersion()
    this.listenTo(ProjectStore, 'change', () => this.forceUpdate())
    window.addEventListener('scroll', this.handleScroll)
  }

  toggleDarkMode = () => {
    const newValue = !Utils.getFlagsmithHasFeature('dark_mode')
    flagsmith.setTrait('dark_mode', newValue)
    if (newValue) {
      document.body.classList.add('dark')
    } else {
      document.body.classList.remove('dark')
    }
  }

  componentDidUpdate(prevProps) {
    if (prevProps.location.pathname !== this.props.location.pathname) {
      if (isMobile) {
        this.setState({ asideIsVisible: false })
      }
      this.hideMobileNav()
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
      this.context.router.history.replace(`/create${query}`)
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
        this.context.router.history.replace(redirect)
      } else {
        AsyncStorage.getItem('lastEnv').then((res) => {
          if (res) {
            const lastEnv = JSON.parse(res)
            const lastOrg = _.find(AccountStore.getUser().organisations, {
              id: lastEnv.orgId,
            })
            if (!lastOrg) {
              this.context.router.history.replace('/projects')
              return
            }

            const org = AccountStore.getOrganisation()
            if (!org || org.id !== lastOrg.id) {
              AppActions.selectOrganisation(lastOrg.id)
              AppActions.getOrganisation(lastOrg.id)
            }

            this.context.router.history.replace(
              `/project/${lastEnv.projectId}/environment/${lastEnv.environmentId}/features`,
            )
            return
          }

          this.context.router.history.replace('/projects')
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
    this.context.router.history.replace('/')
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
    const { asideIsVisible } = this.state
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
    const environmentId = _.get(match, 'params.environmentId')
    const pageHasAside = environmentId || projectId
    const isHomepage =
      pathname === '/' ||
      pathname === '/login' ||
      pathname === '/signup' ||
      pathname.includes('/invite')
    if (Project.amplitude) {
      amplitude.getInstance().init(Project.amplitude)
    }
    if (
      AccountStore.getOrganisation() &&
      AccountStore.getOrganisation().block_access_to_admin
    ) {
      return <Blocked />
    }
    if (Project.maintenance || this.props.error || !window.projectOverrides) {
      return <Maintenance />
    }
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
      return <AccountSettingsPage />
    }
    const projectNotLoaded =
      !ProjectStore.model && document.location.href.includes('project/')
    if (document.location.href.includes('widget')) {
      return <div>{this.props.children}</div>
    }
    if (
      AccountStore.getOrganisation() &&
      AccountStore.getOrganisation().id &&
      this.state.totalApiCalls == 0
    ) {
      getOrganisationUsage(getStore(), {
        organisationId: AccountStore.getOrganisation()?.id,
      }).then((res) => {
        this.setState({ totalApiCalls: res[0]?.data?.totals.total })
      })
    }
    return (
      <Provider store={getStore()}>
        <AccountProvider
          onNoUser={this.onNoUser}
          onLogout={this.onLogout}
          onLogin={this.onLogin}
        >
          {({ isSaving, user }, { twoFactorLogin }) =>
            user && user.twoFactorPrompt ? (
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
              <div>
                <div
                  className={
                    pageHasAside
                      ? `aside-body${
                          isMobile && !asideIsVisible ? '-full-width' : ''
                        }`
                      : ''
                  }
                >
                  {!isHomepage &&
                    (!pageHasAside || !asideIsVisible || !isMobile) && (
                      <nav className='navbar py-0'>
                        <Flex className='flex-row'>
                          <div className='navbar-left'>
                            <div className='navbar-nav'>
                              {pageHasAside && !asideIsVisible && (
                                <div
                                  role='button'
                                  className='clickable toggle mr-4'
                                  onClick={this.toggleAside}
                                >
                                  <span className='icon ion-md-menu' />
                                </div>
                              )}
                              {!projectId && (
                                <a
                                  href={
                                    user ? '/projects' : 'https://flagsmith.com'
                                  }
                                  className='mr-4'
                                >
                                  <img
                                    title='Flagsmith'
                                    height={24}
                                    src='/static/images/nav-logo.svg'
                                    className='brand'
                                    alt='Flagsmith logo'
                                  />
                                </a>
                              )}
                            </div>
                          </div>

                          {user ? (
                            <React.Fragment>
                              <nav className='my-3 my-md-0 hidden-xs-down flex-row navbar-right space'>
                                <Row>
                                  {!!AccountStore.getOrganisation() && (
                                    <NavLink
                                      id='account-settings-link'
                                      data-test='account-settings-link'
                                      activeClassName='active'
                                      className='nav-link'
                                      to={'/projects'}
                                    >
                                      <span className='mr-1'>
                                        <Icon
                                          name='layout'
                                          width={20}
                                          fill='#9DA4AE'
                                        />
                                      </span>
                                      Projects
                                    </NavLink>
                                  )}
                                  <NavLink
                                    id='account-settings-link'
                                    data-test='account-settings-link'
                                    activeClassName='active'
                                    className='nav-link'
                                    to={
                                      projectId
                                        ? `/project/${projectId}/environment/${environmentId}/account`
                                        : '/account'
                                    }
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
                                  {AccountStore.getOrganisationRole() ===
                                  'ADMIN' ? (
                                    <NavLink
                                      id='org-settings-link'
                                      activeClassName='active'
                                      className='nav-link'
                                      to='/organisation-settings'
                                    >
                                      <span className='mr-1'>
                                        <Icon
                                          name='setting'
                                          width={20}
                                          fill='#9DA4AE'
                                        />
                                      </span>
                                      {'Manage'}
                                    </NavLink>
                                  ) : (
                                    !!AccountStore.getOrganisation() && (
                                      <Permission
                                        level='organisation'
                                        permission='MANAGE_USER_GROUPS'
                                        id={AccountStore.getOrganisation().id}
                                      >
                                        {({ permission }) => (
                                          <>
                                            {(!!permission ||
                                              Utils.getFlagsmithHasFeature(
                                                'group_admins',
                                              )) && (
                                              <NavLink
                                                id='org-settings-link'
                                                activeClassName='active'
                                                className='nav-link'
                                                to='/organisation-groups'
                                              >
                                                <span
                                                  style={{ marginRight: 4 }}
                                                >
                                                  <Icon name='setting' />
                                                </span>
                                                {'Manage'}
                                              </NavLink>
                                            )}
                                          </>
                                        )}
                                      </Permission>
                                    )
                                  )}
                                </Row>
                                <Row>
                                  <Button
                                    href='https://docs.flagsmith.com'
                                    target='_blank'
                                    className='btn btn-with-icon mr-2'
                                    size='small'
                                  >
                                    <Icon
                                      name='file-text'
                                      width={20}
                                      fill='#9DA4AE'
                                    />
                                  </Button>
                                  <Headway className='cursor-pointer mr-2' />
                                  <div className='dark-mode mt-0'>
                                    <Switch
                                      checked={Utils.getFlagsmithHasFeature(
                                        'dark_mode',
                                      )}
                                      onChange={this.toggleDarkMode}
                                      darkMode
                                    />
                                  </div>
                                </Row>
                              </nav>
                            </React.Fragment>
                          ) : (
                            <div />
                          )}
                        </Flex>
                      </nav>
                    )}

                  {pageHasAside && (
                    <Aside
                      projectId={projectId}
                      environmentId={environmentId}
                      toggleAside={this.toggleAside}
                      asideIsVisible={asideIsVisible}
                    />
                  )}
                  {isMobile && pageHasAside && asideIsVisible ? null : (
                    <div>
                      <ButterBar />
                      {projectNotLoaded ? (
                        <div className='text-center'>
                          <Loader />
                        </div>
                      ) : (
                        this.props.children
                      )}
                    </div>
                  )}
                </div>
              </div>
            )
          }
        </AccountProvider>
      </Provider>
    )
  }
}

App.propTypes = {
  history: RequiredObject,
  location: RequiredObject,
}

export default withRouter(ConfigProvider(App))

if (E2E) {
  const e2e = document.getElementsByClassName('e2e')
  if (e2e && e2e[0]) {
    e2e[0].classList.toggle('display-none')
  }
}
