module.exports = (envId, _, userId) => `// Identify/create user

curl 'https://edge.api.flagsmith.com/api/v1/identities/?identifier=${userId}'
     -H 'x-environment-key: ${envId}'
`;
