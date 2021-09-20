require('dotenv').config();

const bodyParser = require('body-parser');
const exphbs = require('express-handlebars');
const express = require('express');
const fs = require('fs');
const path = require('path');
const Project = require('../common/project');

const postToSlack = Project.env === 'prod';
const api = require('./api');
const spm = require('./middleware/single-page-middleware');
const webpackMiddleware = require('./middleware/webpack-middleware');
const env = require('../common/project').env;
const slackClient = require('./slack-client');

const SLACK_TOKEN = process.env.SLACK_TOKEN;
const slackMessage = SLACK_TOKEN && require('./slack-client');

const E2E_SLACK_CHANNEL_NAME = process.env.E2E_SLACK_CHANNEL_NAME;

const isDev = process.env.NODE_ENV !== 'production';
const linkedin = process.env.LINKEDIN;

const app = express();
const port = process.env.PORT || 8080;

app.get('/static/project-overrides.js', (req, res) => {
    const getVariable = ({ name, value }) => {
        if (!value) {
            if (typeof value === 'boolean') {
                return `    ${name}: false,`;
            }
            return '';
        }

        if (typeof value !== 'string') {
            return `    ${name}: ${value},`;
        }

        return `    ${name}: '${value}',
        `;
    };
    let sha = '';
    if (fs.existsSync(path.join(__dirname, 'CI_COMMIT_SHA'))) {
        sha = fs.readFileSync(path.join(__dirname, 'CI_COMMIT_SHA'));
    }

    const envToBool = (name, defaultVal) => {
        const envVar = `${process.env[name]}`;
        if (envVar === 'undefined') {
            return defaultVal;
        }
        return envVar === 'true' || envVar === '1';
    };

    const values = [
        { name: 'preventSignup', value: !envToBool('ALLOW_SIGNUPS', true) },
        { name: 'flagsmith', value: process.env.FLAGSMITH_ON_FLAGSMITH_API_KEY },
        { name: 'ga', value: process.env.GOOGLE_ANALYTICS_API_KEY },
        { name: 'crispChat', value: process.env.CRISP_WEBSITE_ID },
        { name: 'sha', value: sha },
        { name: 'mixpanel', value: process.env.MIXPANEL_API_KEY },
        { name: 'sentry', value: process.env.SENTRY_API_KEY },
        { name: 'api', value: process.env.FLAGSMITH_PROXY_API_URL ? '/api/v1/' : process.env.FLAGSMITH_API_URL },
        { name: 'maintenance', value: process.env.ENABLE_MAINTENANCE_MODE },
        { name: 'assetURL', value: process.env.STATIC_ASSET_CDN_URL },
        { name: 'flagsmithClientAPI', value: process.env.FLAGSMITH_ON_FLAGSMITH_API_URL },
        { name: 'disableInflux', value: !envToBool('ENABLE_INFLUXDB_FEATURES', true) },
        { name: 'flagsmithAnalytics', value: envToBool('ENABLE_FLAG_EVALUATION_ANALYTICS', true) },
        { name: 'amplitude', value: process.env.AMPLITUDE_API_KEY },
        { name: 'capterraKey', value: !!process.env.CAPTERRA_API_KEY },
    ];
    const output = values.map(getVariable).join('');

    res.setHeader('content-type', 'text/javascript');
    res.send(`window.projectOverrides = {
        ${output}
    };
    `);
});

app.get('/api/project-overrides', (req, res) => {
    const getVariable = ({ name, value }) => {
        if (!value || value === 'undefined') {
            if (typeof value === 'boolean') {
                return `    ${name}: false,
                `;
            }
            return '';
        }

        if (typeof value !== 'string') {
            return `    ${name}: ${value},
            `;
        }

        return `    ${name}: '${value}',
        `;
    };
    let sha = '';
    if (fs.existsSync(path.join(__dirname, 'CI_COMMIT_SHA'))) {
        sha = fs.readFileSync(path.join(__dirname, 'CI_COMMIT_SHA'));
    }

    const envToBool = (name, defaultVal) => {
        const envVar = `${process.env[name]}`;
        if (envVar === 'undefined') {
            return defaultVal;
        }
        return envVar === 'true' || envVar === '1';
    };

    const values = [
        { name: 'preventSignup', value: !envToBool('ALLOW_SIGNUPS', true) },
        { name: 'flagsmith', value: process.env.FLAGSMITH_ON_FLAGSMITH_API_KEY },
        { name: 'ga', value: process.env.GOOGLE_ANALYTICS_API_KEY },
        { name: 'crispChat', value: process.env.CRISP_WEBSITE_ID },
        { name: 'sha', value: sha },
        { name: 'mixpanel', value: process.env.MIXPANEL_API_KEY },
        { name: 'sentry', value: process.env.SENTRY_API_KEY },
        { name: 'api', value: process.env.FLAGSMITH_PROXY_API_URL ? '/api/v1/' : process.env.FLAGSMITH_API_URL },
        { name: 'maintenance', value: process.env.ENABLE_MAINTENANCE_MODE },
        { name: 'assetURL', value: process.env.STATIC_ASSET_CDN_URL },
        { name: 'flagsmithClientAPI', value: process.env.FLAGSMITH_ON_FLAGSMITH_API_URL },
        { name: 'disableInflux', value: !envToBool('ENABLE_INFLUXDB_FEATURES', true) },
        { name: 'flagsmithAnalytics', value: envToBool('ENABLE_FLAG_EVALUATION_ANALYTICS', true) },
        { name: 'amplitude', value: process.env.AMPLITUDE_API_KEY },
        { name: 'capterraKey', value: process.env.CAPTERRA_API_KEY },
    ];
    const output = values.map(getVariable).join('');

    res.setHeader('content-type', 'text/javascript');
    res.send(`window.projectOverrides = {
        ${output}
    };
    `);
});

// Optionally proxy the API to get around CSRF issues, exposing the API to the world
// PROXY_API_URL should end with the hostname and not /api/v1/
// e.g. PROXY_API_URL=http://api.flagsmith.com/
if (process.env.PROXY_API_URL) {
    const { createProxyMiddleware } = require('http-proxy-middleware');
    app.use('/api/v1/', createProxyMiddleware({ target: process.env.FLAGSMITH_PROXY_API_URL, changeOrigin: true }));
}

if (isDev) { // Serve files from src directory and use webpack-dev-server
    console.log('Enabled Webpack Hot Reloading');
    webpackMiddleware(app);
    app.set('views', 'web/');
    app.use(express.static('web'));
} else { // Serve files from build directory
    console.log('Running production mode');
    app.use(express.static('build'));
    app.set('views', 'build/');
}

app.engine('handlebars', exphbs());
app.set('view engine', 'handlebars');

// Some infrastructure (e.g. Kubernetes) needs simple healthchecks
app.get('/health', (req, res) => {
    console.log('Healthcheck complete');
    res.send('OK');
});

app.get('/robots.txt', (req, res) => {
    res.send('User-agent: *\r\nDisallow: /');
});

// parse various different custom JSON types as JSON
app.use(bodyParser.json());

app.use('/api', api());
app.use(spm);
app.get('/', (req, res) => {
    if (isDev) {
        return res.render('index', {
            isDev,
        });
    }
    return res.render('static/index', {
        isDev,
        linkedin,
    });
});

app.post('/api/event', (req, res) => {
    res.json({ });
    try {
        const body = req.body;
        const channel = body.tag ? `infra_${body.tag.replace(/ /g, '').toLowerCase()}` : process.env.EVENTS_SLACK_CHANNEL;

        if (process.env.SLACK_TOKEN && channel && postToSlack && !body.event.includes('Bullet Train')) {
            const match = body.event.match(/([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})/);
            let url = '';
            if (match && match[0]) {
                const urlMatch = match[0].split('@')[1];
                url = ` https://www.similarweb.com/website/${urlMatch}`;
            }
            slackClient(body.event + url, channel);
        }
    } catch (e) {

    }
});

app.post('/api/webhook', (req, res) => {
    try {
        const body = req.body;
        let message = '';
        res.json(body);
        if (body.data) {
            const state = body.data.new_state;
            if (state.identity_identifier) {
                message = `\`${env} webhook:\` ${body.data.changed_by} changed \`${state.feature.name}\` to \`${state.feature.type === 'FLAG' ? state.enabled : state.feature_state_value || state.feature.initial_value}\` for user \`${state.identity_identifier}(${state.identity})\``;
            } else {
                message = `\`${env} webhook:\` ${body.data.changed_by} changed \`${state.feature.name}\` to \`${state.feature.type === 'FLAG' ? state.enabled : state.feature_state_value || state.feature.initial_value}\``;
            }
            if (slackMessage) {
                slackMessage(message, E2E_SLACK_CHANNEL_NAME);
            }
        }
    } catch (e) {
        console.log(e);
        res.json({ error: e.message || e });
    }
});

if (process.env.SLACK_TOKEN && process.env.DEPLOYMENT_SLACK_CHANNEL && postToSlack) {
    slackClient('Server started', process.env.DEPLOYMENT_SLACK_CHANNEL);
}

app.listen(port, () => {
    console.log(`Server listening on: ${port}`);
});
