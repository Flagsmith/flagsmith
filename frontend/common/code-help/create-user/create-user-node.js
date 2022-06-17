module.exports = (envId, { FEATURE_NAME, FEATURE_NAME_ALT }, userId) => `const Flagsmith = require('flagsmith-nodejs');

const flagsmith = new Flagsmith(
    environmentKey: '${envId}'
);

// Identify the user
const flags = await flagsmith.getIdentityFlags('${userId}', traitList);

// get the state / value of the user's flags 
var showButton = flags.isFeatureEnabled('${FEATURE_NAME}');
var buttonData = flags.getFeatureValue('${FEATURE_NAME_ALT}');
`;
