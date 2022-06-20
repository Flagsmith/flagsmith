module.exports = (envId) => `
curl 'https://edge.api.flagsmith.com/api/v1/flags/'
     -H 'x-environment-key: ${envId}'
`;
