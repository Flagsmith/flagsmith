import Constants from 'common/constants'

module.exports = (envId) => `
curl -i '${Constants.getFlagsmithSDKUrl()}flags/' \\
     -H 'x-environment-key: ${envId}'
`
