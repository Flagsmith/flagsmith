import Constants from 'common/constants'

module.exports = (serversideEnvironmentKey) => `
curl -i '${Constants.getFlagsmithSDKUrl()}environment-document/' \\
     -H 'x-environment-key: ${serversideEnvironmentKey}' | tee flagsmith.json
`
