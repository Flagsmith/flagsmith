import Constants from 'common/constants'

export default (serversideEnvironmentKey) => `
curl -i '${Constants.getFlagsmithSDKUrl()}environment-document/' \\
     -H 'X-Environment-Key: ${serversideEnvironmentKey}' | tee flagsmith.json
`
