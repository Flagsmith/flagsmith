module.exports = (serversideEnvironmentKey) => `
curl -i 'https://edge.api.flagsmith.com/api/v1/environment-document/' \\
     -H 'x-environment-key: ${serversideEnvironmentKey}' | tee flagsmith.json
`
