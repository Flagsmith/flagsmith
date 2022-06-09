module.exports = (envId, { LIB_NAME, NPM_RN_CLIENT, USER_ID, USER_FEATURE_FUNCTION, USER_FEATURE_NAME }, userId) => `// Identify / create user
curl 'https://edge.api.flagsmith.com/api/v1/identities/?identifier=${userId}' -H 'authority: edge.api.flagsmith.com' -H 'x-environment-key: ${envId}' --compressed
`;
