module.exports = (envId, { LIB_NAME, FEATURE_NAME, TRAIT_NAME, USER_ID, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT, NPM_NODE_CLIENT }, userId) => `const Flagsmith = require('flagsmith-nodejs');

const flagsmith = new Flagsmith(
    environmentKey: '${envId}'
);

// This will create a user in the dashboard if they don't already exist
const identifier = 'delboy@trotterstraders.co.uk';
const traitList = { car_type: 'robin_reliant' };

const flags = await flagsmith.getIdentityFlags(identifier, traitList);
var showButton = flags.isFeatureEnabled('secret_button');
var buttonData = flags.getFeatureValue('secret_button');
`;
