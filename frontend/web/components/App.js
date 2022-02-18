import React, { Component } from 'react';
import { matchPath } from 'react-router';
import { withRouter } from 'react-router-dom';
import amplitude from 'amplitude-js';
import NavLink from 'react-router-dom/NavLink';
import Aside from './Aside';
import Popover from './base/Popover';
import Feedback from './modals/Feedback';
import PaymentModal from './modals/Payment';
import AlertBar from './AlertBar';
import TwoFactorPrompt from './SimpleTwoFactor/prompt';
import Maintenance from './Maintenance';
import Blocked from './Blocked';
import AppLoader from './AppLoader';
import ButterBar from './ButterBar';
import UserSettingsIcon from './svg/UserSettingsIcon';
import DocumentationIcon from './svg/DocumentationIcon';
import ArrowUpIcon from './svg/ArrowUpIcon';
import RebrandBanner from './RebrandBanner';
import UpgradeIcon from './svg/UpgradeIcon';
import SparklesIcon from './svg/SparklesIcon';
import AccountSettingsPage from './pages/AccountSettingsPage';
import Headway from "./Headway";

const App = class extends Component {
    static propTypes = {
        children: propTypes.element.isRequired,
    };

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    state = {
        asideIsVisible: !isMobile,
        pin: '',
    };

    constructor(props, context) {
        super(props, context);
        ES6Component(this);
    }

    componentDidMount = () => {
        window.addEventListener('scroll', this.handleScroll);
    };

    toggleDarkMode = () => {
        const newValue = !flagsmith.hasFeature('dark_mode');
        flagsmith.setTrait('dark_mode', newValue);
        if (newValue) {
            document.body.classList.add('dark');
        } else {
            document.body.classList.remove('dark');
        }
    };

    componentWillReceiveProps(nextProps) {
        if (this.props.location.pathname !== nextProps.location.pathname) {
            if (isMobile) {
                this.setState({ asideIsVisible: false });
            }
            this.hideMobileNav();
        }
    }

    hideMobileNav = () => {
        if (this.mobileNav && this.mobileNav.isActive()) {
            this.mobileNav.toggle();
        }
    };

    toggleAside = () => {
        this.setState({ asideIsVisible: !this.state.asideIsVisible });
    };

    onLogin = () => {
        let { redirect } = Utils.fromParam();
        const invite = API.getInvite();
        if (invite) {
            redirect = `/invite/${invite}`;
        }

        const referrer = API.getReferrer();
        let query = '';
        if (referrer) {
            query = `?${Utils.toParam(referrer)}`;
        }

        if (AccountStore.ephemeral_token) {
            this.forceUpdate();
            return;
        }

        if (!AccountStore.getOrganisation() && !invite) { // If user has no organisation redirect to /create
            this.context.router.history.replace(`/create${query}`);
            return;
        }

        // Redirect on login
        if (this.props.location.pathname == '/' || this.props.location.pathname == '/saml' || this.props.location.pathname.includes('/oauth') || this.props.location.pathname == '/login' || this.props.location.pathname == '/demo' || this.props.location.pathname == '/signup') {
            if (redirect) {
                this.context.router.history.replace(redirect);
            } else {
                AsyncStorage.getItem('lastEnv')
                    .then((res) => {
                        if (res) {
                            const lastEnv = JSON.parse(res);
                            const lastOrg = _.find(AccountStore.getUser().organisations, { id: lastEnv.orgId });
                            if (!lastOrg) {
                                this.context.router.history.replace('/projects');
                                return;
                            }

                            const org = AccountStore.getOrganisation();
                            if (!org || org.id !== lastOrg.id) {
                                AppActions.selectOrganisation(lastOrg.id);
                                AppActions.getOrganisation(lastOrg.id);
                            }

                            this.context.router.history.replace(`/project/${lastEnv.projectId}/environment/${lastEnv.environmentId}/features`);
                            return;
                        }

                        this.context.router.history.replace('/projects');
                    });
            }
        }


        if (flagsmith.hasFeature('dark_mode')) {
            document.body.classList.add('dark');
        }
    };

    handleScroll = () => {
        if (this.scrollPos < 768 && $(document)
            .scrollTop() >= 768) {
            this.setState({ myClassName: 'scrolled' });
        } else if (this.scrollPos >= 768 && $(document)
            .scrollTop() < 768) {
            this.setState({ myClassName: '' });
        }
        this.scrollPos = $(document)
            .scrollTop();
    };

    onLogout = () => {
        if (document.location.href.includes('saml?')) {
            return;
        }
        this.context.router.history.replace('/');
    };

    feedback = () => {
        openModal('Feedback', <Feedback />);
    };

    render() {
        if (flagsmith.hasFeature('dark_mode') && !document.body.classList.contains('dark')) {
            document.body.classList.add('dark');
        }
        const {
            match: { params },
            location,
        } = this.props;
        const pathname = location.pathname;
        const { asideIsVisible } = this.state;
        const match = matchPath(pathname, {
            path: '/project/:projectId/environment/:environmentId',
            exact: false,
            strict: false,
        });
        const match2 = matchPath(pathname, {
            path: '/project/:projectId',
            exact: false,
            strict: false,
        });
        const projectId = _.get(match, 'params.projectId') || _.get(match2, 'params.projectId');
        const environmentId = _.get(match, 'params.environmentId');
        const pageHasAside = environmentId || projectId;
        const isHomepage = pathname == '/' || pathname == '/login' || pathname == '/signup' || pathname.includes('/invite');
        if (Project.amplitude) {
            amplitude.getInstance()
                .init(Project.amplitude);
        }
        if (AccountStore.getOrganisation() && (AccountStore.getOrganisation().block_access_to_admin)) {
            return <Blocked />;
        }
        if (Project.maintenance || this.props.error || !window.projectOverrides) {
            return (
                <Maintenance />
            );
        }
        if (this.props.isLoading) {
            return (
                <AccountProvider onNoUser={this.onNoUser} onLogout={this.onLogout} onLogin={this.onLogin}>
                    {() => (
                        <div id="login-page">
                            <AppLoader />
                        </div>
                    )}
                </AccountProvider>
            );
        }
        if (AccountStore.forced2Factor()) {
            return <AccountSettingsPage/>;
        }
        return (
            <div>
                <AccountProvider onNoUser={this.onNoUser} onLogout={this.onLogout} onLogin={this.onLogin}>
                    {({
                        isLoading,
                        isSaving,
                        user,
                        organisation,
                    }, { twoFactorLogin }) => (user && user.twoFactorPrompt ? (
                        <div className="col-md-6 push-md-3 mt-5">
                            <TwoFactorPrompt
                              pin={this.state.pin}
                              error={this.state.error}
                              onSubmit={() => {
                                  this.setState({ error: false });
                                  twoFactorLogin(this.state.pin, () => {
                                      this.setState({ error: true });
                                  });
                              }}
                              isLoading={isSaving}
                              onChange={e => this.setState({ pin: Utils.safeParseEventValue(e) })}
                            />
                        </div>
                    ) : (
                        <div>
                            {AccountStore.isDemo && (
                                <AlertBar preventClose className="pulse">
                                    <div>
                                        You are using a demo account. Finding this useful?
                                        {' '}
                                        <Link onClick={() => AppActions.setUser(null)} to="/">
                                            Click here to Sign
                                            up
                                        </Link>
                                    </div>
                                </AlertBar>
                            )}
                            <div
                              className={pageHasAside ? `aside-body${isMobile && !asideIsVisible ? '-full-width' : ''}` : ''}
                            >
                                {!isHomepage && (!pageHasAside || !asideIsVisible || !isMobile) && (
                                    <nav
                                      className="navbar"
                                    >
                                        <Row space>
                                            <div className="navbar-left">
                                                <div className="navbar-nav">
                                                    {pageHasAside && !asideIsVisible && (
                                                        <div
                                                          role="button" className="clickable toggle"
                                                          onClick={this.toggleAside}
                                                        >
                                                            <span className="icon ion-md-menu" />
                                                        </div>
                                                    )}
                                                    {!projectId && (
                                                        <a href={user ? '/projects' : 'https://flagsmith.com'}>
                                                            <img
                                                              title="Flagsmith" height={24}
                                                              src="/images/nav-logo.svg"
                                                              className="brand" alt="Flagsmith logo"
                                                            />
                                                        </a>
                                                    )}
                                                </div>
                                            </div>
                                            <Row className="navbar-right">
                                                {user ? (
                                                    <React.Fragment>
                                                        <nav className="my-2 my-md-0 hidden-xs-down">
                                                            {organisation && !organisation.subscription && flagsmith.hasFeature('payments_enabled') && (
                                                                <a
                                                                  href="#"
                                                                  disabled={!this.state.manageSubscriptionLoaded}
                                                                  className="cursor-pointer nav-link p-2"
                                                                  onClick={() => {
                                                                      openModal('Payment plans', <PaymentModal
                                                                        viewOnly={false}
                                                                      />, null, { large: true });
                                                                  }}
                                                                >
                                                                    <UpgradeIcon />
                                                                    Upgrade
                                                                </a>
                                                            )}
                                                            <SparklesIcon />
                                                            <Headway className={"nav-link"}/>
                                                            <a
                                                              href="https://docs.flagsmith.com"
                                                              target="_blank" className="nav-link p-2"
                                                            >
                                                                <DocumentationIcon />
                                                                Docs
                                                            </a>
                                                            <NavLink
                                                              id="account-settings-link"
                                                              activeClassName="active"
                                                              className="nav-link"
                                                              to={projectId ? `/project/${projectId}/environment/${environmentId}/account` : '/account'}
                                                            >
                                                                <UserSettingsIcon />
                                                                Account
                                                            </NavLink>
                                                            {AccountStore.getOrganisationRole() === 'ADMIN' && (
                                                            <NavLink
                                                              id="org-settings-link"
                                                              activeClassName="active"
                                                              className="nav-link"
                                                              to="/organisation-settings"
                                                            >
                                                                <ion style={{ marginRight: 4 }} className="icon--primary ion ion-md-settings"/>
                                                                {'Manage'}
                                                            </NavLink>
                                                            )}
                                                        </nav>
                                                        <div style={{ marginRight: 16, marginTop: 0 }} className="dark-mode">
                                                            <Switch
                                                              checked={flagsmith.hasFeature('dark_mode')} onChange={this.toggleDarkMode} onMarkup="Light"
                                                              offMarkup="Dark"
                                                            />
                                                        </div>
                                                        <div className="org-nav">
                                                            <Popover
                                                              className="popover-right"
                                                              contentClassName="popover-bt"
                                                              renderTitle={toggle => (
                                                                  <a
                                                                    className="nav-link" id="org-menu"
                                                                    onClick={toggle}
                                                                  >
                                                                      <span className="nav-link-featured relative">
                                                                          {organisation ? organisation.name : ''}
                                                                          <span
                                                                            className="flex-column ion ion-ios-arrow-down"
                                                                          />
                                                                      </span>
                                                                  </a>
                                                              )}
                                                            >
                                                                {toggle => (
                                                                    <div className="popover-inner__content">
                                                                        <span
                                                                          className="popover-bt__title"
                                                                        >Organisations
                                                                        </span>
                                                                        {organisation && (
                                                                            <OrganisationSelect
                                                                              projectId={projectId}
                                                                              environmentId={environmentId}
                                                                              clearableValue={false}
                                                                              onChange={(organisation) => {
                                                                                  toggle();
                                                                                  AppActions.selectOrganisation(organisation.id);
                                                                                  AppActions.getOrganisation(organisation.id);
                                                                                  this.context.router.history.push('/projects');
                                                                              }}
                                                                            />
                                                                        )}
                                                                        {!this.props.hasFeature('disable_create_org') && (!projectOverrides.superUserCreateOnly || (projectOverrides.superUserCreateOnly && AccountStore.model.is_superuser)) && (
                                                                            <div className="pl-3 pr-3 mt-2 mb-2">
                                                                                <Link
                                                                                  id="create-org-link" onClick={toggle}
                                                                                  to="/create"
                                                                                >
                                                                                    <Flex className="text-center">
                                                                                        <Button>Create Organisation <span className="ion-md-add"/></Button>
                                                                                    </Flex>
                                                                                </Link>
                                                                            </div>
                                                                        )}
                                                                        <a
                                                                          id="logout-link" href="#"
                                                                          onClick={AppActions.logout}
                                                                          className="popover-bt__list-item"
                                                                        >
                                                                            <img
                                                                              src="/images/icons/aside/logout-dark.svg"
                                                                              className="mr-2"
                                                                            />
                                                                            Logout
                                                                        </a>
                                                                    </div>
                                                                )}
                                                            </Popover>
                                                        </div>
                                                    </React.Fragment>
                                                ) : (
                                                    <div />
                                                )}

                                            </Row>
                                        </Row>
                                    </nav>
                                )}
                                {pageHasAside && (
                                    <Aside
                                      className={`${AccountStore.isDemo ? 'demo' : ''} ${AccountStore.isDemo ? 'footer' : ''}`}
                                      projectId={projectId}
                                      environmentId={environmentId}
                                      toggleAside={this.toggleAside}
                                      asideIsVisible={asideIsVisible}
                                    />
                                )}
                                {isMobile && pageHasAside && asideIsVisible ? null : (
                                    <div>
                                        <ButterBar/>
                                        {this.props.children}
                                    </div>
                                )}

                            </div>
                        </div>
                    ))}
                </AccountProvider>

            </div>
        );
    }
};

App.propTypes = {
    location: RequiredObject,
    history: RequiredObject,
};

export default withRouter(ConfigProvider(App));
