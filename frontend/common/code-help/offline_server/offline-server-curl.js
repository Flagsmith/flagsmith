module.exports = (serversideEnvironmentKey) => `
curl 'https://edge.api.flagsmith.com/api/v1/environment-document/'\\
     -H 'x-environment-key: ${serversideEnvironmentKey}' > flagsmith.json
`
