module.exports = (envId, { TRAIT_NAME, USER_ID }, userId) => `const Flagsmith = require('flagsmith-nodejs');

const flagsmith = new Flagsmith(
    environmentKey: '${envId}'
);

// Identify a user, set their traits and retrieve the flags
const traits = { ${TRAIT_NAME}: 'robin_reliant' };
const flags = await flagsmith.getIdentityFlags('${USER_ID}', traits);
`;
