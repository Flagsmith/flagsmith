const _globalThis = typeof window === 'undefined' ? global : window
const Project = {
  api: 'http://localhost:8000/api/v1/',
  chargebee: {
    site: 'flagsmith-test',
  },

  debug: false,

  env: 'dev',

  flagsmith: 'ENktaJnfLVbLifybz34JmX',

  flagsmithClientAPI: 'https://edge.api.flagsmith.com/api/v1/',

  flagsmithClientEdgeAPI: 'https://edge.api.flagsmith.com/api/v1/',
  // This is used for Sentry tracking
  maintenance: false,
  plans: {
    scaleUp: { annual: 'scale-up-12-months-v4', monthly: 'scale-up-v4' },
    startup: { annual: 'start-up-12-months-v2', monthly: 'startup-v2' },
  },
  useSecureCookies: false,
  ...(_globalThis.projectOverrides || {}),
}
_globalThis.Project = Project
export default Project
