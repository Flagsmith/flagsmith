/**
 * Created by kylejohnson on 02/08/2016.
 */
 require('colors');
 const fs = require('fs-extra');
 const path = require('path');
 
 const envToBool = (name, defaultVal) => {
     const envVar = `${process.env[name]}`;
     if (envVar === 'undefined') {
         return defaultVal;
     }
     return envVar === 'true' || envVar === '1';
 };
 
 const getVariable = ({ name, value }) => {
     if (!value) {
         return '';
     }
     return `    ${name}: '${value}',
     `;
 };
 
 const env = process.env.ENV || 'dev';
 const src = path.resolve(__dirname, `../env/project_${env}.js`);
 const overrideSrc = path.resolve(__dirname, '../web/static/project-overrides.js');
 const overrideTarget = path.resolve(__dirname, '../build/static/project-overrides.js');
 const target = path.resolve(__dirname, '../common/project.js');
 const buildDir = path.resolve(__dirname, '../build/static');
 
 const values = [
     { name: 'preventSignup', value: !envToBool('ALLOW_SIGNUPS', true) },
     { name: 'flagsmith', value: process.env.FLAGSMITH_ON_FLAGSMITH_API_KEY },
     { name: 'ga', value: process.env.GOOGLE_ANALYTICS_API_KEY },
     { name: 'crispChat', value: process.env.CRISP_WEBSITE_ID },
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
 const config = `window.projectOverrides = {
     ${output}
 };
 `;
 
 fs.writeFileSync(overrideSrc, config);
 
 if (fs.existsSync(buildDir)) {
     fs.copyFileSync(overrideSrc, overrideTarget);
 }
 
 fs.copyFileSync(src, target);
 console.log(`Using project_${env}.js`.green);
 
 fs.copySync(src, target);