module.exports = (envId, { LIB_NAME, NPM_RN_CLIENT, USER_ID, USER_FEATURE_FUNCTION, USER_FEATURE_NAME }, userId) => `
// Identify / create user
curl 'https://api.flagsmith.com/api/v1/identities/?identifier=${userId}' -H 'authority: api.bullet-train.io' -H 'x-environment-key: ${envId}' --compressed
`;
