import Constants from 'common/constants'

export default (envId) => `
curl -i '${Constants.getFlagsmithSDKUrl()}flags/' \\
     -H 'X-Environment-Key: ${envId}'
`
