const globalThis = typeof window === 'undefined' ? global : window
module.exports = global.Project = {
  api: 'https://api.flagsmith.com/api/v1/',

  chargebee: {
    site: 'flagsmith',
  },

  cookieDomain: '.flagsmith.com',

  env: 'prod',

  excludeAnalytics: 'nightwatch@solidstategroup.com',

  // This is our Bullet Train API key - Bullet Train runs on Bullet Train!
  flagsmith: '4vfqhypYjcPoGGu8ByrBaj',

  flagsmithClientAPI: 'https://api.flagsmith.com/api/v1/',

  flagsmithClientEdgeAPI: 'https://edge.api.flagsmith.com/api/v1/',
  // This is used for Sentry tracking
  maintenance: false,
  ...(globalThis.projectOverrides || {}),
}
