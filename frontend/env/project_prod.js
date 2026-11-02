// eslint-disable-next-line @dword-design/import-alias/prefer-alias
import { E2E_CHANGE_MAIL, E2E_SIGN_UP_USER, E2E_USER } from '../e2e/config'

const _globalThis = typeof window === 'undefined' ? global : window
const Project = {
  api: 'https://api.flagsmith.com/api/v1/',

  chargebee: {
    site: 'flagsmith',
  },

  cookieDomain: '.flagsmith.com',

  env: 'prod',

  excludeAnalytics: [E2E_SIGN_UP_USER, E2E_USER, E2E_CHANGE_MAIL],

  // This is our Bullet Train API key - Bullet Train runs on Bullet Train!
  flagsmith: '4vfqhypYjcPoGGu8ByrBaj',

  flagsmithClientAPI: 'https://edge.api.flagsmith.com/api/v1/',

  flagsmithClientEdgeAPI: 'https://edge.api.flagsmith.com/api/v1/',

  flagsmithClientEventsAPI: 'https://events.api.flagsmith.com/',

  hubspot: '//js-eu1.hs-scripts.com/143451822.js',

  // The website's "Contact Enterprise Sales" form, opened by Contact Sales.
  // Production only, so clicks on staging or locally can't create sales leads.
  hubspotContactSalesForm: {
    formId: 'd71fdd04-bb77-485e-af7f-bd9c4e1c3bf5',
    portalId: '143451822',
    region: 'eu1',
  },

  linkedinConversionId: 16798338,
  // This is used for Sentry tracking
  maintenance: false,
  plans: {
    scaleUp: {
      annual: 'Scale-Up-v4-USD-Yearly',
      monthly: 'Scale-Up-v4-USD-Monthly',
    },
    startup: { annual: 'start-up-12-months-v2', monthly: 'startup-v2' },
  },
  useSecureCookies: true,
  ...(_globalThis.projectOverrides || {}),
}
_globalThis.Project = Project
export default Project
