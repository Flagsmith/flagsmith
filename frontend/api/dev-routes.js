// Shared Express routes used by both RspackDevServer (dev) and api/index.js (prod)
require('dotenv').config()
const bodyParser = require('body-parser')

module.exports = function setupRoutes(app) {
  app.get('/config/project-overrides', (req, res) => {
    const getVariable = ({ name, value }) => {
      if (!value || value === 'undefined') {
        if (typeof value === 'boolean') {
          return `    ${name}: false,\n                `
        }
        return ''
      }
      if (typeof value !== 'string') {
        return `    ${name}: ${value},\n            `
      }
      return `    ${name}: '${value.trim()}',\n        `
    }
    const envToBool = (name, defaultVal) => {
      const envVar = `${process.env[name]}`
      if (envVar === 'undefined') {
        return defaultVal
      }
      return envVar === 'true' || envVar === '1'
    }
    const sha = ''
    const values = [
      { name: 'preventSignup', value: envToBool('PREVENT_SIGNUP', false) },
      { name: 'preventEmailPassword', value: envToBool('PREVENT_EMAIL_PASSWORD', false) },
      { name: 'preventForgotPassword', value: envToBool('PREVENT_FORGOT_PASSWORD', false) },
      { name: 'superUserCreateOnly', value: envToBool('ONLY_SUPERUSERS_CAN_CREATE_ORGANISATIONS', false) },
      { name: 'flagsmith', value: process.env.FLAGSMITH_ON_FLAGSMITH_API_KEY },
      { name: 'headway', value: process.env.HEADWAY_API_KEY },
      { name: 'ga', value: process.env.GOOGLE_ANALYTICS_API_KEY },
      { name: 'sha', value: sha },
      { name: 'pylonAppId', value: process.env.PYLON_APP_ID },
      { name: 'fpr', value: process.env.FIRST_PROMOTER_ID },
      { name: 'sentry', value: process.env.SENTRY_API_KEY },
      { name: 'api', value: process.env.FLAGSMITH_PROXY_API_URL ? '/api/v1/' : process.env.FLAGSMITH_API_URL },
      { name: 'apiProxyEnabled', value: !!process.env.FLAGSMITH_PROXY_API_URL },
      { name: 'maintenance', value: envToBool('ENABLE_MAINTENANCE_MODE', false) },
      { name: 'flagsmithClientAPI', value: process.env.FLAGSMITH_ON_FLAGSMITH_API_URL },
      { name: 'disableAnalytics', value: envToBool('DISABLE_ANALYTICS_FEATURES', false) },
      { name: 'flagsmithAnalytics', value: envToBool('ENABLE_FLAG_EVALUATION_ANALYTICS', true) },
      { name: 'flagsmithRealtime', value: envToBool('ENABLE_FLAGSMITH_REALTIME', false) },
      { name: 'amplitude', value: process.env.AMPLITUDE_API_KEY },
      { name: 'reo', value: process.env.REO_API_KEY },
      { name: 'delighted', value: process.env.DELIGHTED_API_KEY },
      { name: 'capterraKey', value: process.env.CAPTERRA_API_KEY },
      { name: 'hideInviteLinks', value: envToBool('DISABLE_INVITE_LINKS', false) },
      { name: 'linkedinPartnerTracking', value: envToBool('LINKEDIN_PARTNER_TRACKING', false) },
      { name: 'albacross', value: process.env.ALBACROSS_CLIENT_ID },
      { name: 'useSecureCookies', value: envToBool('USE_SECURE_COOKIES', true) },
      { name: 'cookieSameSite', value: process.env.USE_SECURE_COOKIES },
      { name: 'cookieAuthEnabled', value: process.env.COOKIE_AUTH_ENABLED },
      { name: 'githubAppURL', value: process.env.GITHUB_APP_URL },
      { name: 'e2eToken', value: process.env[`E2E_TEST_TOKEN_${(process.env.ENV || 'dev').toUpperCase()}`] || process.env.E2E_TEST_TOKEN || '' },
      { name: 'evaluationAnalyticsServerUrl', value: process.env.EVALUATION_ANALYTICS_SERVER_URL },
    ]
    let output = values.map(getVariable).join('')
    res.setHeader('Cache-Control', 's-max-age=1, stale-while-revalidate')
    res.setHeader('content-type', 'application/javascript')
    const e2eScript = process.env.E2E ? 'window.E2E=true;' : ''
    res.send(`${e2eScript}window.projectOverrides = {\n        ${output}\n    };`)
  })

  // Optionally proxy the API
  if (process.env.FLAGSMITH_PROXY_API_URL) {
    const { createProxyMiddleware } = require('http-proxy-middleware')
    app.use(
      '/api/v1/',
      createProxyMiddleware({
        changeOrigin: true,
        target: process.env.FLAGSMITH_PROXY_API_URL,
        xfwd: true,
      }),
    )
  }

  app.use(bodyParser.json())

  app.get('/health', (req, res) => {
    // eslint-disable-next-line
    console.log('Healthcheck complete')
    res.send('OK')
  })
}
