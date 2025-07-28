require('dotenv').config()
const fs = require('fs')
const exphbs = require('express-handlebars')
const express = require('express')
const bodyParser = require('body-parser')
const spm = require('./middleware/single-page-middleware')
const path = require('path')
const app = express()

const SLACK_TOKEN = process.env.SLACK_TOKEN
const slackClient = SLACK_TOKEN && require('./slack-client')

const postToSlack = process.env.VERCEL_ENV === 'production'

const isDev = process.env.NODE_ENV !== 'production'
const port = process.env.PORT || 8080

app.get('/config/project-overrides', (req, res) => {
  const getVariable = ({ name, value }) => {
    if (!value || value === 'undefined') {
      if (typeof value === 'boolean') {
        return `    ${name}: false,
                `
      }
      return ''
    }

    if (typeof value !== 'string') {
      return `    ${name}: ${value},
            `
    }

    return `    ${name}: '${value.trim()}',
        `
  }
  const envToBool = (name, defaultVal) => {
    const envVar = `${process.env[name]}`
    if (envVar === 'undefined') {
      return defaultVal
    }
    return envVar === 'true' || envVar === '1'
  }
  const sha = ''
  /*
    todo: implement across docker and vercel
    if (fs.existsSync(path.join(__dirname, 'CI_COMMIT_SHA'))) {
        sha = fs.readFileSync(path.join(__dirname, 'CI_COMMIT_SHA'));
    }
    */

  const values = [
    { name: 'preventSignup', value: envToBool('PREVENT_SIGNUP', false) },
    {
      name: 'preventEmailPassword',
      value: envToBool('PREVENT_EMAIL_PASSWORD', false),
    },
    {
      name: 'preventForgotPassword',
      value: envToBool('PREVENT_FORGOT_PASSWORD', false),
    },
    {
      name: 'superUserCreateOnly',
      value: envToBool('ONLY_SUPERUSERS_CAN_CREATE_ORGANISATIONS', false),
    },
    { name: 'flagsmith', value: process.env.FLAGSMITH_ON_FLAGSMITH_API_KEY },
    { name: 'headway', value: process.env.HEADWAY_API_KEY },
    { name: 'ga', value: process.env.GOOGLE_ANALYTICS_API_KEY },
    { name: 'sha', value: sha },
    { name: 'crispChat', value: process.env.CRISP_WEBSITE_ID },
    { name: 'fpr', value: process.env.FIRST_PROMOTER_ID },
    { name: 'sentry', value: process.env.SENTRY_API_KEY },
    {
      name: 'api',
      value: process.env.FLAGSMITH_PROXY_API_URL
        ? '/api/v1/'
        : process.env.FLAGSMITH_API_URL,
    },
    { name: 'maintenance', value: envToBool('ENABLE_MAINTENANCE_MODE', false) },
    {
      name: 'flagsmithClientAPI',
      value: process.env.FLAGSMITH_ON_FLAGSMITH_API_URL,
    },
    {
      name: 'disableAnalytics',
      value: envToBool('DISABLE_ANALYTICS_FEATURES', false),
    },
    {
      name: 'flagsmithAnalytics',
      value: envToBool('ENABLE_FLAG_EVALUATION_ANALYTICS', true),
    },
    {
      name: 'flagsmithRealtime',
      value: envToBool('ENABLE_FLAGSMITH_REALTIME', false),
    },
    { name: 'amplitude', value: process.env.AMPLITUDE_API_KEY },
    { name: 'reo', value: process.env.REO_API_KEY },
    { name: 'delighted', value: process.env.DELIGHTED_API_KEY },
    { name: 'capterraKey', value: process.env.CAPTERRA_API_KEY },
    {
      name: 'hideInviteLinks',
      value: envToBool('DISABLE_INVITE_LINKS', false),
    },
    {
      name: 'linkedinPartnerTracking',
      value: envToBool('LINKEDIN_PARTNER_TRACKING', false),
    },
    { name: 'albacross', value: process.env.ALBACROSS_CLIENT_ID },
    { name: 'useSecureCookies', value: envToBool('USE_SECURE_COOKIES', false) },
    { name: 'cookieSameSite', value: process.env.COOKIE_SAME_SITE },
    { name: 'cookieAuthEnabled', value: process.env.COOKIE_AUTH_ENABLED },
    {
      name: 'githubAppURL',
      value: process.env.GITHUB_APP_URL,
    },
    {
      name: 'e2eToken',
      value: process.env.E2E_TEST_TOKEN || '',
    },
  ]
  let output = values.map(getVariable).join('')
  res.setHeader('Cache-Control', 's-max-age=1, stale-while-revalidate')
  res.setHeader('content-type', 'application/javascript')
  res.send(`window.projectOverrides = {
        ${output}
    };`)
})

// Optionally proxy the API to get around CSRF issues, exposing the API to the world
// FLAGSMITH_PROXY_API_URL should end with the hostname and not /api/v1/
// e.g. FLAGSMITH_PROXY_API_URL=http://api.flagsmith.com/
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

if (isDev) {
  // Serve files from src directory and use webpack-dev-server
  // eslint-disable-next-line
  console.log('Enabled Webpack Hot Reloading')
  const webpackMiddleware = require('./middleware/webpack-middleware')
  webpackMiddleware(app)
  app.set('views', 'web/')
  app.use(express.static('web'))
} else {
  if (!process.env.VERCEL) {
    app.use(express.static('public'))
  }
  if (fs.existsSync(path.join(process.cwd(), 'frontend'))) {
    app.set('views', 'frontend/public/static')
  } else {
    app.set('views', 'public/static')
  }
}

app.engine(
  'handlebars',
  exphbs.create({
    defaultLayout: '',
    layoutsDir: '',
  }).engine,
)
app.set('view engine', 'handlebars')

app.get('/robots.txt', (req, res) => {
  res.send('User-agent: *\r\nDisallow: /')
})

app.get('/health', (req, res) => {
  // eslint-disable-next-line
  console.log('Healthcheck complete')
  res.send('OK')
})

app.get('/version', (req, res) => {
  let commitSha = 'Unknown'
  let imageTag = 'Unknown'

  try {
    commitSha = fs
      .readFileSync('CI_COMMIT_SHA', 'utf8')
      .replace(/(\r\n|\n|\r)/gm, '')
  } catch (err) {
    // eslint-disable-next-line
    console.log('Unable to read CI_COMMIT_SHA')
  }

  try {
    let releasePleaseManifest = JSON.parse(
      fs.readFileSync('./.versions.json', 'utf8'),
    )
    res.send({
      'ci_commit_sha': commitSha,
      'image_tag': releasePleaseManifest['.'],
      'package_versions': releasePleaseManifest,
    })
  } catch (err) {
    // eslint-disable-next-line
    console.log('Unable to read .versions.json file')
    res.send({ 'ci_commit_sha': commitSha, 'image_tag': imageTag })
  }
})

app.use(bodyParser.json())
app.use(spm)
const genericWebsite = (url) => {
  if (!url) return true
  if (
    url.includes('hotmail.') ||
    url.includes('gmail.') ||
    url.includes('icloud.') ||
    url.includes('flagsmith.com')
  ) {
    return true
  }
  return false
}
app.post('/api/event', (req, res) => {
  try {
    const body = req.body
    const channel = body.tag
      ? `infra_${body.tag.replace(/ /g, '').toLowerCase()}`
      : process.env.EVENTS_SLACK_CHANNEL
    if (
      process.env.SLACK_TOKEN &&
      channel &&
      postToSlack &&
      !body.event.includes('Bullet Train')
    ) {
      const match = body.event.match(
        /([a-zA-Z0-9_\-.]+)@([a-zA-Z0-9_\-.]+)\.([a-zA-Z]{2,5})/,
      )
      let url = ''
      if (match && match[0]) {
        const urlMatch = match[0].split('@')[1]
        if (!genericWebsite(urlMatch)) {
          url = ` https://www.similarweb.com/website/${urlMatch}`
        }
      }
      slackClient(body.event + url, channel).finally(() => {
        res.json({})
      })
    } else {
      res.json({})
    }
  } catch (e) {
    // eslint-disable-next-line
    console.log(`Error posting to from /api/event:${e}`)
  }
})

app.post('/api/webflow/webhook', (req, res) => {
  if (req.body.name === 'Contact Form') {
    // TODO: process contact form
    return res.status(200).json({})
  } else if (req.body.name === 'Subscribe Form') {
    // TODO: process Subscribe form
    return res.status(200).json({})
  } else {
    return res.status(200).json({})
  }
})

// Catch all to render index template
app.get('/', (req, res) => {
  const linkedin = process.env.LINKEDIN || ''
  return res.render('index', {
    isDev,
    linkedin,
  })
})

app.listen(port, () => {
  // eslint-disable-next-line
  console.log(`Server listening on: ${port}`)
  if (!isDev && process.send) {
    process.send({ done: true })
  }
})

module.exports = app
