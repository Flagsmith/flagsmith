module.exports = (envId, { LIB_NAME, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_NAME_ALT }, userId) => `// Identify/create user

curl 'https://edge.api.flagsmith.com/api/v1/identities/?identifier=${userId}'
     -H 'x-environment-key: ${envId}'
`;
