module.exports = (envId, userId) => `// Identify / create user
curl 'https://edge.api.flagsmith.com/api/v1/identities/?identifier=${userId}' -H 'authority: edge.api.flagsmith.com' -H 'x-environment-key: ${envId}' --compressed
`;
