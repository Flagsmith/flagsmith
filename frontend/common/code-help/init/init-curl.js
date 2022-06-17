module.exports = (envId) => `
curl 'https://edge.api.flagsmith.com/api/v1/flags/' -H 'authority: edge.api.flagsmith.com' -H 'x-environment-key: ${envId}' --compressed
`;
