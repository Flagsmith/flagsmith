import { E2E_CHANGE_MAIL, E2E_SIGN_UP_USER, E2E_USER } from '../e2e/config'

const globalThis = typeof window === 'undefined' ? global : window
module.exports = global.Project = {
  api: 'https://api.flagsmith.com/api/v1/',

  chargebee: {
    site: 'flagsmith',
  },

  cookieDomain: '.flagsmith.com',

  env: 'prod',

  excludeAnalytics: [E2E_SIGN_UP_USER, E2E_USER, E2E_CHANGE_MAIL],

  // This is our Bullet Train API key - Bullet Train runs on Bullet Train!
  flagsmith: '4vfqhypYjcPoGGu8ByrBaj',

  flagsmithClientAPI: 'https://api.flagsmith.com/api/v1/',

  flagsmithClientEdgeAPI: 'https://edge.api.flagsmith.com/api/v1/',

  hubspot: '//js-eu1.hs-scripts.com/143451822.js',

  linkedinConversionId: 16798338,
  // This is used for Sentry tracking
  maintenance: false,
  plans: {
    scaleUp: { annual: 'scale-up-12-months-v2', monthly: 'scale-up-v2' },
    startup: { annual: 'start-up-12-months-v2', monthly: 'startup-v2' },
  },
  useSecureCookies: true,
  ...(globalThis.projectOverrides || {}),
}
