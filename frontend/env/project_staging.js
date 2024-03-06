const globalThis = typeof window === 'undefined' ? global : window
module.exports = global.Project = {
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
  useSecureCookies: true,
  ...(globalThis.projectOverrides || {}),
}
