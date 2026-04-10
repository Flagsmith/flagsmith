const _globalThis = typeof window === 'undefined' ? global : window
const Project = {
  api: 'https://api-staging.flagsmith.com/api/v1/',

  chargebee: {
    site: 'flagsmith-test',
  },

  env: 'staging',

  // This is our Bullet Train API key - Bullet Train runs on Bullet Train!
  flagsmith: 'ENktaJnfLVbLifybz34JmX',

  flagsmithClientAPI: 'https://edge.api.flagsmith.com/api/v1/',

  flagsmithClientEdgeAPI: 'https://edge.bullet-train-staging.win/api/v1/',
  // This is used for Sentry tracking
  maintenance: false,
  plans: {
    scaleUp: { annual: 'Scale-Up-v4-USD-Yearly', monthly: 'Scale-Up-v4-USD-Monthly' },
    startup: { annual: 'start-up-12-months-v2', monthly: 'startup-v2' },
  },
  useSecureCookies: true,
  ...(_globalThis.projectOverrides || {}),
}
_globalThis.Project = Project
export default Project
