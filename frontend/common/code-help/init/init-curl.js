module.exports = (envId, { LIB_NAME, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, customFeature) => `
curl 'https://edge.api.flagsmith.com/api/v1/flags/' -H 'authority: edge.api.flagsmith.com' -H 'x-environment-key: ${envId}' --compressed
`;
