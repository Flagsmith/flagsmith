import Constants from 'common/constants'

module.exports = (envId) => `
curl -i '${Constants.getFlagsmithSDKUrl()}flags/' \\
     -H 'X-Environment-Key: ${envId}'
`
