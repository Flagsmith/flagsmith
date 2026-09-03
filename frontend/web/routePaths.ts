import { matchPath } from 'react-router-dom'

// The route table on its own, so anything needing a path does not have to
// import the component tree. web/routes imports App, so reading it from a
// component is a cycle.
export const routes = {
  'account': '/account',
  'account-settings': '/project/:projectId/environment/:environmentId/account',
  'admin-dashboard': '/admin/dashboard',
  'audit-log': '/project/:projectId/audit-log',
  'audit-log-item': '/project/:projectId/audit-log/:id',
  'broken': '/broken',
  'change-request':
    '/project/:projectId/environment/:environmentId/change-requests/:id',
  'change-request-project': '/project/:projectId/change-requests/:id',
  'change-requests':
    '/project/:projectId/environment/:environmentId/change-requests',
  'change-requests-project': '/project/:projectId/change-requests',
  'compare': '/project/:projectId/compare',
  'create-environment': '/project/:projectId/environment/create',
  'create-organisation': '/create',
  'create-release-pipeline': '/project/:projectId/release-pipelines/create',
  'dev-view': '/organisation/:organisationId/dev-view',
  'environment-settings':
    '/project/:projectId/environment/:environmentId/settings',
  'executive-view': '/organisation/:organisationId/executive-view',
  'experiment-detail':
    '/project/:projectId/environment/:environmentId/experiments/:experimentId',
  'experiments': '/project/:projectId/environment/:environmentId/experiments',
  'feature-history': '/project/:projectId/environment/:environmentId/history',
  'feature-history-detail':
    '/project/:projectId/environment/:environmentId/history/:id/',
  'features': '/project/:projectId/environment/:environmentId/features',
  'flag-environments': '/project/:projectId/flag/:flagId/environments',
  'gettingStarted': '/getting-started',
  'github-setup': '/github-setup',
  'home': '/home',
  'identities': '/project/:projectId/environment/:environmentId/identities',
  'identity':
    '/project/:projectId/environment/:environmentId/identities/:identity/:id',
  'identity-id':
    '/project/:projectId/environment/:environmentId/identities/:identity',
  'integrations': '/project/:projectId/integrations',
  'invite': '/invite/:id',
  'invite-link': '/invite-link/:id',
  'legacy-identities': '/project/:projectId/environment/:environmentId/users',
  'legacy-identity':
    '/project/:projectId/environment/:environmentId/users/:identity/:id',
  'legacy-identity-id':
    '/project/:projectId/environment/:environmentId/users/:identity',
  'lifecycle': '/project/:projectId/lifecycle/:section?',
  'login': '/login',
  'maintenance': '/maintenance',
  'metrics': '/project/:projectId/environment/:environmentId/metrics',
  'not-found': '/404',
  'oauth': '/oauth/:type',
  'oauth-authorize': '/oauth/authorize',
  'organisation-integrations': '/organisation/:organisationId/integrations',
  'organisation-permissions': '/organisation/:organisationId/permissions',
  'organisation-projects': '/organisation/:organisationId/projects',
  'organisation-settings': '/organisation/:organisationId/settings',
  'organisation-settings-redirect': '/organisation-settings',
  'organisation-usage': '/organisation/:organisationId/usage',
  'organisations': '/organisations',
  'password-reset': '/password-reset/confirm/:uid/:token/',
  'permissions': '/project/:projectId/permissions',
  'project-redirect': '/project/:projectId',
  'project-settings': '/project/:projectId/settings',
  'project-settings-in-environment':
    '/project/:projectId/environment/:environmentId/project-settings',
  'release-manager': '/organisation/:organisationId/release-manager',
  'release-pipelines': '/project/:projectId/release-pipelines',
  'release-pipelines-detail': '/project/:projectId/release-pipelines/:id',
  'release-pipelines-detail-edit':
    '/project/:projectId/release-pipelines/:id/edit',
  'root': '/',
  'saml': '/saml',
  'scheduled-change':
    '/project/:projectId/environment/:environmentId/scheduled-changes/:id',
  'scheduled-changes':
    '/project/:projectId/environment/:environmentId/scheduled-changes',
  'sdk-keys': '/project/:projectId/environment/:environmentId/sdk-keys',
  'segment': '/project/:projectId/segments/:id',
  'segments': '/project/:projectId/segments',
  'signup': '/signup',
}

// A blocked organisation keeps the organisations list, to switch away, and the
// usage page, which explains the block.
export const ALLOWED_WHILE_BLOCKED = [
  routes.organisations,
  routes['organisation-usage'],
]

export const isAllowedWhileBlocked = (pathname: string): boolean =>
  ALLOWED_WHILE_BLOCKED.some((path) =>
    matchPath(pathname, { exact: true, path, strict: false }),
  )
