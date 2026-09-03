import React from 'react'
import { Route, Switch } from 'react-router-dom'

import App from './components/App' // App Wrapper
import HomePage from './components/pages/home-page'
import Maintenance from './components/Maintenance'
import CreateOrganisationPage from './components/pages/CreateOrganisationPage'
import CreateEnvironmentPage from './components/pages/CreateEnvironmentPage'
import IdentitiesPage from './components/pages/IdentitiesPage'
import IdentityPage from './components/pages/IdentityPage'
import IdentityIdPage from './components/pages/IdentityIdPage'
import IntegrationsPage from './components/pages/IntegrationsPage'
import FlagsPage from './components/pages/features'
import SegmentsPage from './components/pages/SegmentsPage'
import OrganisationSettingsPage from './components/pages/organisation-settings'
import AccountSettingsPage from './components/pages/AccountSettingsPage'
import NotFoundErrorPage from './components/pages/NotFoundErrorPage'
import ProjectSettingsPage from './components/pages/project-settings'
import PasswordResetPage from './components/pages/PasswordResetPage'
import EnvironmentSettingsPage from './components/pages/environment-settings'
import InvitePage from './components/pages/InvitePage'
import NotFoundPage from './components/pages/NotFoundPage'
import ChangeRequestsPage from './components/pages/ChangeRequestsPage'
import ChangeRequestDetailPage from './components/pages/ChangeRequestDetailPage'
import ScheduledChangesPage from './components/pages/ScheduledChangesPage'
import AuditLogPage from './components/pages/AuditLogPage'
import ComparePage from './components/pages/ComparePage'
import BrokenPage from './components/pages/BrokenPage'
import GitHubSetupPage from './components/pages/GitHubSetupPage'
import AuditLogItemPage from './components/pages/AuditLogItemPage'
import ProjectsPage from './components/ProjectsPage'
import OrganisationSettingsRedirectPage from './components/pages/OrganisationSettingsRedirectPage'
import OrganisationUsagePage from './components/pages/OrganisationUsagePage'
import OrganisationsPage from './components/pages/OrganisationsPage'
import UsersAndPermissionsPage from './components/pages/UsersAndPermissionsPage'
import ProjectRedirectPage from './components/pages/ProjectRedirectPage'
import { SDKKeysPage } from './components/pages/sdk-keys'
import { ParameterizedRoute } from './components/base/higher-order/ParameterizedRoute'
import FeatureHistoryDetailPage from './components/pages/FeatureHistoryDetailPage'
import OrganisationIntegrationsPage from './components/pages/OrganisationIntegrationsPage'
import ProjectChangeRequestsPage from './components/pages/ProjectChangeRequestsPage'
import ProjectChangeRequestPage from './components/pages/ProjectChangeRequestDetailPage'
import GettingStartedGate from './components/pages/onboarding/GettingStartedGate'

import ReleasePipelinesPage from './components/pages/ReleasePipelinesPage'
import CreateReleasePipelinePage from './components/pages/CreateReleasePipelinePage'
import ReleasePipelineDetailPage from './components/pages/ReleasePipelineDetailPage'
import SegmentPage from './components/pages/SegmentPage'
import ExperimentsPage from './components/pages/ExperimentsPage'
import ExperimentDetailPage from './components/pages/ExperimentDetailPage'
import MetricsPage from './components/pages/MetricsPage'
import ReleaseManagerPage from './components/pages/ReleaseManagerPage'
import FlagEnvironmentsPage from './components/pages/FlagEnvironmentsPage'
import ExecutiveViewPage from './components/pages/ExecutiveViewPage'
import DevViewPage from './components/pages/DevViewPage'
import AdminDashboardPage from './components/pages/admin-dashboard/AdminDashboardPage'
import CleanupPage from './components/pages/feature-lifecycle'
import OAuthAuthorizePage from './components/pages/OAuthAuthorizePage'
import { routes } from './routePaths'
import { Provider } from 'react-redux'
import { getStore } from 'common/store'
export { routes } from './routePaths'
export default (
  <Switch>
    <Route path={routes['oauth-authorize']} exact>
      <Provider store={getStore()}>
        <OAuthAuthorizePage />
      </Provider>
    </Route>
    <App>
      <Switch>
        <Route path={routes.root} exact component={HomePage} />
        <Route path={routes.login} exact component={HomePage} />
        <Route path={routes['not-found']} exact component={NotFoundErrorPage} />
        <Route path={routes.signup} exact component={HomePage} />
        <Route path={routes.home} exact component={HomePage} />
        <Route
          path={routes['github-setup']}
          exact
          component={GitHubSetupPage}
        />
        <Route path={routes.maintenance} exact component={Maintenance} />
        <Route
          path={routes['password-reset']}
          exact
          component={PasswordResetPage}
        />
        <ParameterizedRoute
          path={routes.features}
          exact
          component={FlagsPage}
        />
        <ParameterizedRoute
          path={routes.experiments}
          exact
          component={ExperimentsPage}
        />
        <ParameterizedRoute
          path={routes['experiment-detail']}
          exact
          component={ExperimentDetailPage}
        />
        <ParameterizedRoute
          path={routes.metrics}
          exact
          component={MetricsPage}
        />
        <ParameterizedRoute
          path={routes.lifecycle}
          exact
          component={CleanupPage}
        />
        <ParameterizedRoute
          path={routes['change-requests']}
          exact
          component={ChangeRequestsPage}
        />
        <ParameterizedRoute
          path={routes['change-requests-project']}
          exact
          component={ProjectChangeRequestsPage}
        />
        <ParameterizedRoute
          path={routes['change-request-project']}
          exact
          component={ProjectChangeRequestPage}
        />
        <ParameterizedRoute
          path={routes['scheduled-changes']}
          exact
          component={ScheduledChangesPage}
        />
        <ParameterizedRoute
          path={routes['change-request']}
          exact
          component={ChangeRequestDetailPage}
        />
        <ParameterizedRoute
          path={routes['scheduled-change']}
          exact
          component={ChangeRequestDetailPage}
        />
        <Route path={routes.invite} exact component={InvitePage} />
        <Route path={routes['invite-link']} exact component={InvitePage} />
        <Route path={routes.broken} exact component={BrokenPage} />
        <Route path={routes.oauth} exact component={HomePage} />
        <Route path={routes.saml} exact component={HomePage} />
        <ParameterizedRoute
          path={routes['environment-settings']}
          exact
          component={EnvironmentSettingsPage}
        />
        <ParameterizedRoute
          path={routes['sdk-keys']}
          exact
          component={SDKKeysPage}
        />
        <ParameterizedRoute
          path={routes.integrations}
          exact
          component={IntegrationsPage}
        />
        <ParameterizedRoute
          path={routes['organisation-integrations']}
          exact
          component={OrganisationIntegrationsPage}
        />
        <ParameterizedRoute
          path={routes.identities}
          exact
          component={IdentitiesPage}
        />
        <ParameterizedRoute
          path={routes['identity-id']}
          exact
          component={IdentityIdPage}
        />
        <ParameterizedRoute
          path={routes.identity}
          exact
          component={IdentityPage}
        />
        {/* Legacy /users routes for backward compatibility */}
        <ParameterizedRoute
          path={routes['legacy-identities']}
          exact
          component={IdentitiesPage}
        />
        <ParameterizedRoute
          path={routes['legacy-identity-id']}
          exact
          component={IdentityIdPage}
        />
        <ParameterizedRoute
          path={routes['legacy-identity']}
          exact
          component={IdentityPage}
        />
        <ParameterizedRoute
          path={routes['create-environment']}
          exact
          component={CreateEnvironmentPage}
        />
        <ParameterizedRoute
          path={routes.gettingStarted}
          exact
          component={GettingStartedGate}
        />
        <ParameterizedRoute
          path={routes['project-settings-in-environment']}
          exact
          component={ProjectSettingsPage}
        />
        <ParameterizedRoute
          path={routes.compare}
          exact
          component={ComparePage}
        />
        <ParameterizedRoute
          path={routes['feature-history-detail']}
          exact
          component={FeatureHistoryDetailPage}
        />
        <ParameterizedRoute
          path={routes['project-settings']}
          exact
          component={ProjectSettingsPage}
        />
        <ParameterizedRoute
          path={routes.permissions}
          exact
          component={ProjectSettingsPage}
        />
        <ParameterizedRoute
          path={routes.segments}
          exact
          component={SegmentsPage}
        />
        <ParameterizedRoute
          path={routes.segment}
          exact
          component={SegmentPage}
        />
        <ParameterizedRoute
          path={routes['organisation-settings']}
          exact
          component={OrganisationSettingsPage}
        />
        <ParameterizedRoute
          path={routes['organisation-permissions']}
          exact
          component={UsersAndPermissionsPage}
        />
        <ParameterizedRoute
          path={routes['organisation-usage']}
          exact
          component={OrganisationUsagePage}
        />
        <ParameterizedRoute
          path={routes['release-manager']}
          exact
          component={ReleaseManagerPage}
        />
        <ParameterizedRoute
          path={routes['executive-view']}
          exact
          component={ExecutiveViewPage}
        />
        <ParameterizedRoute
          path={routes['dev-view']}
          exact
          component={DevViewPage}
        />
        <ParameterizedRoute
          path={routes['flag-environments']}
          exact
          component={FlagEnvironmentsPage}
        />
        <Route
          path={routes['organisation-settings-redirect']}
          exact
          component={OrganisationSettingsRedirectPage}
        />
        <ParameterizedRoute
          path={routes['organisation-projects']}
          exact
          component={ProjectsPage}
        />
        <ParameterizedRoute
          path={routes['account-settings']}
          exact
          component={AccountSettingsPage}
        />
        <ParameterizedRoute
          path={routes['project-redirect']}
          exact
          component={ProjectRedirectPage}
        />
        <ParameterizedRoute
          path={routes['release-pipelines']}
          exact
          component={ReleasePipelinesPage}
        />
        <ParameterizedRoute
          path={routes['create-release-pipeline']}
          exact
          component={CreateReleasePipelinePage}
        />
        <ParameterizedRoute
          path={routes['release-pipelines-detail']}
          exact
          component={ReleasePipelineDetailPage}
        />
        <ParameterizedRoute
          path={routes['release-pipelines-detail-edit']}
          exact
          component={CreateReleasePipelinePage}
        />
        <ParameterizedRoute
          path={routes['audit-log-item']}
          exact
          component={AuditLogItemPage}
        />
        <Route path={routes.account} exact component={AccountSettingsPage} />
        <ParameterizedRoute
          path={routes['audit-log']}
          exact
          component={AuditLogPage}
        />
        <Route
          path={routes.organisations}
          exact
          component={OrganisationsPage}
        />
        <ParameterizedRoute
          path={routes['audit-log-item']}
          exact
          component={AuditLogItemPage}
        />
        <Route
          path={routes['create-organisation']}
          exact
          component={CreateOrganisationPage}
        />
        <Route
          path={routes['admin-dashboard']}
          exact
          component={AdminDashboardPage}
        />
        <Route path='*' component={NotFoundPage} />
      </Switch>
    </App>
  </Switch>
)
