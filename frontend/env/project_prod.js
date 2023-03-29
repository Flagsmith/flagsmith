const globalThis = typeof window === 'undefined' ? global : window
module.exports = global.Project = {
  api: 'https://api.flagsmith.com/api/v1/',

  chargebee: {
    site: 'flagsmith',
  },

  // trigger maintenance mode
  cookieDomain: '.flagsmith.com',

  demoAccount: {
    email: 'kyle+bullet-train@solidstategroup.com',
    password: 'demo_account',
  },

  // This is our Bullet Train API key - Bullet Train runs on Bullet Train!
  env: 'prod',

  excludeAnalytics: 'nightwatch@solidstategroup.com',

  flagsmith: '4vfqhypYjcPoGGu8ByrBaj',

  flagsmithClientAPI: 'https://api.flagsmith.com/api/v1/',

  flagsmithClientEdgeAPI: 'https://edge.api.flagsmith.com/api/v1/',
  // This is used for Sentry tracking
  maintenance: false,
  ...(globalThis.projectOverrides || {}),
}
