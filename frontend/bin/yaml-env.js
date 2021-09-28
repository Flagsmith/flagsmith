/**
 * Created by kylejohnson on 02/08/2016.
 */
require('colors');
const fs = require('fs');
const extra = require('fs');
const path = require('path');

const src = path.resolve(__dirname, '../app.yaml');
let str = extra.readFileSync(src, 'utf8');
str += `
env_variables:
  SLACK_TOKEN: ${process.env.SLACK_TOKEN}
  EVENTS_SLACK_CHANNEL: ${process.env.EVENTS_SLACK_CHANNEL}
  FLAGSMITH_ON_FLAGSMITH_API_KEY: ${process.env.FLAGSMITH_ON_FLAGSMITH_API_KEY}
  FLAGSMITH_ANALYTICS: ${process.env.ENABLE_FLAG_EVALUATION_ANALYTICS}
  GOOGLE_ANALYTICS_API_KEY: ${process.env.GOOGLE_ANALYTICS_API_KEY}
  CRISP_WEBSITE_ID: ${process.env.CRISP_WEBSITE_ID}
  CAPTERRA_API_KEY: ${process.env.CAPTERRA_API_KEY}
  LINKEDIN: ${process.env.LINKEDIN}
  ALLOW_SIGNUPS: ${process.env.ALLOW_SIGNUPS}
  MIXPANEL: ${process.env.MIXPANEL_API_KEY}
  FLAGSMITH_API_URL: ${process.env.FLAGSMITH_API_URL}
  AMPLITUDE: ${process.env.AMPLITUDE_API_KEY}
  DELIGHTED_API_KEY: ${process.env.DELIGHTED_API_KEY}
  ENABLE_MAINTENANCE_MODE: ${process.env.ENABLE_MAINTENANCE_MODE}
  ENABLE_INFLUXDB_FEATURES: ${process.env.ENABLE_INFLUXDB_FEATURES}
  STATIC_ASSET_CDN_URL: ${process.env.STATIC_ASSET_CDN_URL}
`;

fs.writeFileSync(src, str);
