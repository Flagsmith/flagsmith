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
import FeatureHistoryPage from './components/pages/FeatureHistoryPage'
import Utils from 'common/utils/utils'
import ProjectsPage from './components/ProjectsPage'
import OrganisationSettingsRedirectPage from './components/pages/OrganisationSettingsRedirectPage'
import OrganisationUsagePage from './components/pages/OrganisationUsagePage'
import OrganisationsPage from './components/pages/OrganisationsPage'
import UsersAndPermissionsPage from './components/pages/UsersAndPermissionsPage'
import ProjectRedirectPage from './components/pages/ProjectRedirectPage'
import SDKKeysPage from './components/SDKKeysPage'
import { ParameterizedRoute } from './components/base/higher-order/ParameterizedRoute'

export default (
  <App>
    <Switch>
      <Route path='/' exact component={HomePage} />
      <Route path='/login' exact component={HomePage} />
      <Route path='/404' exact component={NotFoundErrorPage} />
      <Route path='/signup' exact component={HomePage} />
      <Route path='/home' exact component={HomePage} />
      {Utils.getFlagsmithHasFeature('github_integration') && (
        <Route path='/github-setup' exact component={GitHubSetupPage} />
      )}
      <Route path='/maintenance' exact component={Maintenance} />
      <Route
        path='/password-reset/confirm/:uid/:token/'
        exact
        component={PasswordResetPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/features'
        exact
        component={FlagsPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/change-requests'
        exact
        component={ChangeRequestsPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/scheduled-changes'
        exact
        component={ScheduledChangesPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/change-requests/:id'
        exact
        component={ChangeRequestPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/scheduled-changes/:id'
        exact
        component={ChangeRequestPage}
      />
      <Route path='/widget' exact component={WidgetPage} />
      <Route path='/invite/:id' exact component={InvitePage} />
      <Route path='/invite-link/:id' exact component={InvitePage} />
      <Route path='/broken' exact component={BrokenPage} />
      <Route path='/oauth/:type' exact component={HomePage} />
      <Route path='/saml' exact component={HomePage} />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/settings'
        exact
        component={EnvironmentSettingsPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/sdk-keys'
        exact
        component={SDKKeysPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/integrations'
        exact
        component={IntegrationsPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/users'
        exact
        component={UsersPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/users/:identity'
        exact
        component={UserIdPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/users/:identity/:id'
        exact
        component={UserPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/create'
        exact
        component={CreateEnvironmentPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/project-settings'
        exact
        component={ProjectSettingsPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/compare'
        exact
        component={ComparePage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/history'
        exact
        component={FeatureHistoryPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/settings'
        exact
        component={ProjectSettingsPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/permissions'
        exact
        component={ProjectSettingsPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/segments'
        exact
        component={SegmentsPage}
      />
      <ParameterizedRoute
        path='/organisation/:organisationId/settings'
        exact
        component={OrganisationSettingsPage}
      />
      <ParameterizedRoute
        path='/organisation/:organisationId/permissions'
        exact
        component={UsersAndPermissionsPage}
      />
      <ParameterizedRoute
        path='/organisation/:organisationId/usage'
        exact
        component={OrganisationUsagePage}
      />
      <Route
        path='/organisation-settings'
        exact
        component={OrganisationSettingsRedirectPage}
      />
      <ParameterizedRoute
        path='/organisation/:organisationId/projects'
        exact
        component={ProjectsPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/account'
        exact
        component={AccountSettingsPage}
      />
      <ParameterizedRoute
        path='/project/:projectId'
        exact
        component={ProjectRedirectPage}
      />
      <Route path='/account' exact component={AccountSettingsPage} />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/audit-log'
        exact
        component={AuditLogPage}
      />
      <ParameterizedRoute
        path='/project/:projectId/audit-log'
        exact
        component={AuditLogPage}
      />
      <Route path='/organisations' exact component={OrganisationsPage} />
      <ParameterizedRoute
        path='/project/:projectId/environment/:environmentId/audit-log/:id'
        exact
        component={AuditLogItemPage}
      />
      <Route path='/create' exact component={CreateOrganisationPage} />
      <Route path='*' component={NotFoundPage} />
    </Switch>
  </App>
)
