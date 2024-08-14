module.exports = (serversideEnvironmentKey) => `
curl -i '${Project.flagsmithClientAPI}environment-document/' \\
     -H 'x-environment-key: ${serversideEnvironmentKey}' | tee flagsmith.json
`
