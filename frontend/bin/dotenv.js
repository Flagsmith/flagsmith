const fs = require('fs');

const res = `
  SLACK_TOKEN="${process.env.SLACK_TOKEN || ''}"
  E2E_SLACK_CHANNEL="${process.env.E2E_SLACK_CHANNEL || ''}"
  E2E_SLACK_CHANNEL_NAME="${process.env.E2E_SLACK_CHANNEL_NAME || ''}"
`;
fs.writeFileSync('./.env', res);
