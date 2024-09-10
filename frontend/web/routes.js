import React from 'react'
import { Route, Switch } from 'react-router-dom'

import App from './components/App' // App Wrapper
import HomePage from './components/pages/HomePage'
import Maintenance from './components/Maintenance'
import CreateOrganisationPage from './components/pages/CreateOrganisationPage'
import CreateEnvironmentPage from './components/pages/CreateEnvironmentPage'
import UsersPage from './components/pages/UsersPage'
import UserPage from './components/pages/UserPage'
import UserIdPage from './components/pages/UserIdPage'
import IntegrationsPage from './components/pages/IntegrationsPage'
import FlagsPage from './components/pages/FeaturesPage'
import SegmentsPage from './components/pages/SegmentsPage'
import OrganisationSettingsPage from './components/pages/OrganisationSettingsPage'
import AccountSettingsPage from './components/pages/AccountSettingsPage'
import NotFoundErrorPage from './components/pages/NotFoundErrorPage'
import ProjectSettingsPage from './components/pages/ProjectSettingsPage'
import PasswordResetPage from './components/pages/PasswordResetPage'
import EnvironmentSettingsPage from './components/pages/EnvironmentSettingsPage'
import InvitePage from './components/pages/InvitePage'
import NotFoundPage from './components/pages/NotFoundPage'
import ChangeRequestsPage from './components/pages/ChangeRequestsPage'
import ChangeRequestPage from './components/pages/ChangeRequestPage'
import ScheduledChangesPage from './components/pages/ScheduledChangesPage'
import AuditLogPage from './components/pages/AuditLogPage'
import ComparePage from './components/pages/ComparePage'
import WidgetPage from './components/pages/WidgetPage'
import BrokenPage from './components/pages/BrokenPage'
import GitHubSetupPage from './components/pages/GitHubSetupPage'
import AuditLogItemPage from './components/pages/AuditLogItemPage'
import Utils from 'common/utils/utils'
import ProjectsPage from './components/ProjectsPage'
import OrganisationSettingsRedirectPage from './components/pages/OrganisationSettingsRedirectPage'
import OrganisationUsagePage from './components/pages/OrganisationUsagePage'
import OrganisationsPage from './components/pages/OrganisationsPage'
import UsersAndPermissionsPage from './components/pages/UsersAndPermissionsPage'
import ProjectRedirectPage from './components/pages/ProjectRedirectPage'
import SDKKeysPage from './components/SDKKeysPage'
import { ParameterizedRoute } from './components/base/higher-order/ParameterizedRoute'
import FeatureHistoryDetailPage from './components/pages/FeatureHistoryDetailPage'

export const routes = {
  'broken': '/broken',
  'change-request':
    '/project/:projectId/environment/:environmentId/change-requests/:id',
  'change-requests':
    '/project/:projectId/environment/:environmentId/change-requests',
  'environment-settings':
    '/project/:projectId/environment/:environmentId/settings',
  'features': '/project/:projectId/environment/:environmentId/features',
  'github-setup': '/github-setup',
  'home': '/home',
  'integrations': '/project/:projectId/integrations',
  'invite': '/invite/:id',
  'create-environment': '/project/:projectId/environment/create',
  'invite-link': '/invite-link/:id',
  'compare': '/project/:projectId/compare',
  'login': '/login',
  'feature-history': '/project/:projectId/environment/:environmentId/history',
  'maintenance': '/maintenance',
  'feature-history-detail':
    '/project/:projectId/environment/:environmentId/history/:id/',
  'not-found': '/404',
  'oauth': '/oauth/:type',
  'organisation-settings': '/organisation/:organisationId/settings',
  'organisation-permissions': '/organisation/:organisationId/permissions',
  'root': '/',
  'organisation-settings-redirect': '/organisation-settings',
  'account-settings': '/project/:projectId/environment/:environmentId/account',
  'signup': '/signup',
  'audit-log': '/project/:projectId/audit-log',
  'audit-log-item': '/project/:projectId/audit-log/:id',
  'password-reset': '/password-reset/confirm/:uid/:token/',
  'create-organisation': '/create',
  'scheduled-change':
    '/project/:projectId/environment/:environmentId/scheduled-changes/:id',
  'account': '/account',
  'scheduled-changes':
    '/project/:projectId/environment/:environmentId/scheduled-changes',
  'organisation-projects': '/organisation/:organisationId/projects',
  'organisation-usage': '/organisation/:organisationId/usage',
  'widget': '/widget',
  'organisations': '/organisations',
  'permissions': '/project/:projectId/permissions',
  'saml': '/saml',
  'project-redirect': '/project/:projectId',
  'sdk-keys': '/project/:projectId/environment/:environmentId/sdk-keys',
  'project-settings': '/project/:projectId/settings',
  'user-id': '/project/:projectId/environment/:environmentId/users/:identity',
  'project-settings-in-environment':
    '/project/:projectId/environment/:environmentId/project-settings',
  'users': '/project/:projectId/environment/:environmentId/users',
  'segments': '/project/:projectId/segments',
  'user': '/project/:projectId/environment/:environmentId/users/:identity/:id',
}
export default (
  <App>
    <Switch>
      <Route path={routes.root} exact component={HomePage} />
      <Route path={routes.login} exact component={HomePage} />
      <Route path={routes['not-found']} exact component={NotFoundErrorPage} />
      <Route path={routes.signup} exact component={HomePage} />
      <Route path={routes.home} exact component={HomePage} />
      {Utils.getFlagsmithHasFeature('github_integration') && (
        <Route
          path={routes['github-setup']}
          exact
          component={GitHubSetupPage}
        />
      )}
      <Route path={routes.maintenance} exact component={Maintenance} />
      <Route
        path={routes['password-reset']}
        exact
        component={PasswordResetPage}
      />
      <ParameterizedRoute path={routes.features} exact component={FlagsPage} />
      <ParameterizedRoute
        path={routes['change-requests']}
        exact
        component={ChangeRequestsPage}
      />
      <ParameterizedRoute
        path={routes['scheduled-changes']}
        exact
        component={ScheduledChangesPage}
      />
      <ParameterizedRoute
        path={routes['change-request']}
        exact
        component={ChangeRequestPage}
      />
      <ParameterizedRoute
        path={routes['scheduled-change']}
        exact
        component={ChangeRequestPage}
      />
      <Route path={routes.widget} exact component={WidgetPage} />
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
      <ParameterizedRoute path={routes.users} exact component={UsersPage} />
      <ParameterizedRoute
        path={routes['user-id']}
        exact
        component={UserIdPage}
      />
      <ParameterizedRoute path={routes.user} exact component={UserPage} />
      <ParameterizedRoute
        path={routes['create-environment']}
        exact
        component={CreateEnvironmentPage}
      />
      <ParameterizedRoute
        path={routes['project-settings-in-environment']}
        exact
        component={ProjectSettingsPage}
      />
      <ParameterizedRoute path={routes.compare} exact component={ComparePage} />
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
      <Route path={routes.account} exact component={AccountSettingsPage} />
      <ParameterizedRoute
        path={routes['audit-log']}
        exact
        component={AuditLogPage}
      />
      <Route path={routes.organisations} exact component={OrganisationsPage} />
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
      <Route path='*' component={NotFoundPage} />
    </Switch>
  </App>
)
