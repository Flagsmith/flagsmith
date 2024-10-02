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
  plans: {
    scaleUp: { annual: 'scale-up-annual-v2', monthly: 'scale-up-v2' },
    startup: { annual: 'startup-annual-v2', monthly: 'startup-v2' },
  },
  useSecureCookies: true,
  ...(globalThis.projectOverrides || {}),
}
