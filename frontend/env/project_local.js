const _globalThis = typeof window === 'undefined' ? global : window
const Project = {
  api: 'http://localhost:8000/api/v1/',
  chargebee: {
    site: 'flagsmith-test',
  },

  // Local dev is served over plain HTTP, so cookies cannot be Secure. Browsers
  // reject SameSite=None cookies that are not Secure, which would drop the auth
  // cookie on every page load.
  cookieSameSite: 'lax',

  debug: false,

  env: 'dev',

  flagsmith: 'ENktaJnfLVbLifybz34JmX',

  flagsmithClientAPI: 'https://edge.api.flagsmith.com/api/v1/',

  flagsmithClientEdgeAPI: 'https://edge.api.flagsmith.com/api/v1/',

  flagsmithClientEventsAPI: 'https://events.bullet-train-staging.win/',
  // This is used for Sentry tracking
  maintenance: false,
  plans: {
    scaleUp: {
      annual: 'Scale-Up-v4-USD-Yearly',
      monthly: 'Scale-Up-v4-USD-Monthly',
    },
    startup: { annual: 'startup-annual-v2', monthly: 'startup-v2' },
  },
  useSecureCookies: false,
  ...(_globalThis.projectOverrides || {}),
}
_globalThis.Project = Project
export default Project
