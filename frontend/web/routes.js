import React from 'react';
import { Route, Switch } from 'react-router-dom';

import App from './components/App'; // App Wrapper
import HomePage from './components/pages/HomePage';
import DemoPage from './components/pages/DemoPage';
import Maintenance from './components/Maintenance';
import ProjectSelectPage from './components/pages/ProjectSelectPage';
import CreateOrganisationPage from './components/pages/CreateOrganisationPage';
import CreateEnvironmentPage from './components/pages/CreateEnvironmentPage';
import UsersPage from './components/pages/UsersPage';
import UserPage from './components/pages/UserPage';
import IntegrationsPage from './components/pages/IntegrationsPage';
import FlagsPage from './components/pages/FeaturesPage';
import SegmentsPage from './components/pages/SegmentsPage';
import OrganisationSettingsPage from './components/pages/OrganisationSettingsPage';
import AccountSettingsPage from './components/pages/AccountSettingsPage';
import NotFoundErrorPage from './components/pages/NotFoundErrorPage';
import ProjectSettingsPage from './components/pages/ProjectSettingsPage';
import PasswordResetPage from './components/pages/PasswordResetPage';
import EnvironmentSettingsPage from './components/pages/EnvironmentSettingsPage';
import InvitePage from './components/pages/InvitePage';
import NotFoundPage from './components/pages/NotFoundPage';
import PricingPage from './components/pages/PricingPage';
import TermsPoliciesPage from './components/pages/TermsPoliciesPage';
import AuditLogPage from './components/pages/AuditLogPage';
import CompareEnvironmentsPage from './components/pages/CompareEnvironmentsPage';

export default (
    <App>
        <Switch>
            <Route path="/" exact component={HomePage}/>
            {/* <Route path="/markup" exact component={MarkupPage}/> */}
            <Route path="/login" exact component={HomePage}/>
            <Route path="/404" exact component={NotFoundErrorPage}/>
            <Route path="/signup" exact component={HomePage}/>
            <Route path="/demo" exact component={DemoPage}/>
            <Route path="/signup" exact component={HomePage}/>
            <Route path="/home" exact component={HomePage}/>
            <Route path="/pricing" exact component={PricingPage}/>
            <Route path="/legal/:section" exact component={TermsPoliciesPage}/>
            <Route path="/legal" exact component={TermsPoliciesPage}/>
            <Route path="/projects" exact component={ProjectSelectPage}/>
            <Route path="/maintenance" exact component={Maintenance}/>
            <Route path="/password-reset/confirm/:uid/:token/" exact component={PasswordResetPage}/>
            <Route path="/project/:projectId/environment/:environmentId/features" exact component={FlagsPage}/>
            <Route path="/invite/:id" exact component={InvitePage}/>
            <Route path="/oauth/:type" exact component={HomePage}/>
            <Route path="/saml" exact component={HomePage}/>
            <Route path="/project/:projectId/environment/:environmentId/settings" exact component={EnvironmentSettingsPage}/>
            <Route path="/project/:projectId/integrations" exact component={IntegrationsPage}/>
            <Route path="/project/:projectId/environment/:environmentId/users" exact component={UsersPage}/>
            <Route path="/project/:projectId/environment/:environmentId/users/:identity/:id" exact component={UserPage}/>
            <Route path="/project/:projectId/environment/create" exact component={CreateEnvironmentPage}/>
            <Route path="/project/:projectId/environment/:environmentId/project-settings" exact component={ProjectSettingsPage}/>
            <Route path="/project/:projectId/environment/:environmentId/compare" exact component={CompareEnvironmentsPage}/>
            <Route path="/project/:projectId/settings" exact component={ProjectSettingsPage}/>
            <Route path="/project/:projectId/environment/:environmentId/segments" exact component={SegmentsPage}/>
            <Route path="/project/:projectId/environment/:environmentId/organisation-settings" exact component={OrganisationSettingsPage}/>
            <Route path="/organisation-settings" exact component={OrganisationSettingsPage}/>
            <Route path="/project/:projectId/environment/:environmentId/account" exact component={AccountSettingsPage}/>
            <Route path="/account" exact component={AccountSettingsPage}/>
            <Route path="/project/:projectId/environment/:environmentId/audit-log" exact component={AuditLogPage}/>
            <Route path="/project/:projectId/audit-log" exact component={AuditLogPage}/>
            <Route path="/create" exact component={CreateOrganisationPage}/>
            <Route component={NotFoundPage}/>
        </Switch>
    </App>
);
