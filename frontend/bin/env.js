/**
 * Created by kylejohnson on 02/08/2016.
 */
require('colors');
const fs = require('fs');
const path = require('path');

const env = process.env.ENV || 'dev';
const src = path.resolve(__dirname, `../env/project_${env}.js`);
const overrideSrc = path.resolve(__dirname, '../web/static/project-overrides.js');
const overrideTarget = path.resolve(__dirname, '../build/static/project-overrides.js');
const target = path.resolve(__dirname, '../common/project.js');
const buildDir = path.resolve(__dirname, '../build/static');
const getVariable = ({ name, value }) => {
    if (!value) {
        return '';
    }
    return `    ${name}: '${value}',
    `;
};

const values = [
    { name: 'preventSignup', value: process.env.PREVENT_SIGNUP },
    { name: 'flagsmith', value: process.env.FLAGSMITH },
    { name: 'ga', value: process.env.GA },
    { name: 'crispChat', value: process.env.CRISP_CHAT },
    { name: 'mixpanel', value: process.env.MIXPANEL },
    { name: 'sentry', value: process.env.SENTRY },
    { name: 'api', value: process.env.API_URL },
    { name: 'maintenance', value: process.env.MAINTENANCE },
    { name: 'assetURL', value: process.env.ASSET_URL },
    { name: 'flagsmithAnalytics', value: process.env.FLAGSMITH_ANALYTICS },
    { name: 'flagsmithClientAPI', value: process.env.FLAGSMITH_CLIENT_API },
    { name: 'amplitude', value: process.env.AMPLITUDE },
];
const output = values.map(getVariable).join('');
const config = `window.projectOverrides = {
    ${output}
};
`;

fs.writeFileSync(overrideSrc, config);

if (fs.existsSync(buildDir)) {
    fs.copyFileSync(overrideSrc, overrideTarget);
}

fs.copyFileSync(src, target);
