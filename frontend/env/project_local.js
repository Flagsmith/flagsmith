const globalThis = typeof window === 'undefined' ? global : window
module.exports = global.Project = {
  api: 'http://localhost:8000/api/v1/',
  chargebee: {
    site: 'flagsmith-test',
  },

  debug: false,

  // trigger maintenance mode
  demoAccount: {
    email: 'kyle+bullet-train@solidstategroup.com',
    password: 'demo_account',
  },

  env: 'dev',

  flagsmith: 'ENktaJnfLVbLifybz34JmX',

  flagsmithClientAPI: 'https://api.flagsmith.com/api/v1/',

  flagsmithClientEdgeAPI: 'https://edge.api.flagsmith.com/api/v1/',
  // This is used for Sentry tracking
  maintenance: false,
  ...(globalThis.projectOverrides || {}),
}
