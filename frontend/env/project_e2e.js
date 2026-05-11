const _globalThis = typeof window === 'undefined' ? global : window
const Project = {
  api: 'http://flagsmith-api:8000/api/v1/',

  chargebee: {
    site: 'flagsmith-test',
  },

  // This is our Bullet Train API key - Bullet Train runs on Bullet Train!
  debug: false,

  env: 'dev',

  flagsmith: 'ENktaJnfLVbLifybz34JmX',

  flagsmithClientAPI: 'https://edge.api.flagsmith.com/api/v1/',

  flagsmithClientEdgeAPI: 'https://edge.api.flagsmith.com/api/v1/',
  // This is used for Sentry tracking
  maintenance: false,
  useSecureCookies: true,
  ...(_globalThis.projectOverrides || {}),
}
_globalThis.Project = Project
export default Project
