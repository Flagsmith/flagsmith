import Constants from 'common/constants'

module.exports = (serversideEnvironmentKey) => `
curl -i '${Constants.getFlagsmithSDKUrl()}environment-document/' \\
     -H 'X-Environment-Key: ${serversideEnvironmentKey}' | tee flagsmith.json
`
